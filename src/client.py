import socket
import logging 
import struct
import xml.etree.ElementTree as et

HOST = "localhost"
PORT = 8000

OP_GET_ENTITIES = 1
OP_GET_QUERIES = 2
OP_GET_FEEDBACKS = 3
OP_NEW_ENTITY = 4
OP_NEW_QUERY = 5
OP_NEW_FEEDBACK = 6
OP_EDIT_ENTITY = 7
OP_EDIT_QUERY = 8
OP_EDIT_FEEDBACK = 9
OP_DEL_ENTITY = 10
OP_DEL_QUERY = 11
OP_DEL_FEEDBACK = 12

logging.basicConfig(
    filename = "journal.log",
    filemode = "a",
    encoding = "utf-8",
    level = logging.INFO,
    format = "%(asctime)s opcode=%(opcode)s size=%(size)s xml=%(xml)s"
)

def recv_exact(sock: socket.socket, n: int) -> bytes:
    buff = b""
    while len(buff) < n:
        chunk = sock.recv(n - len(buff))
        if not chunk:
            raise ConnectionError("Server closed connection")
        buff += chunk
    return buff

class RpcClient:
    def __init__(self, host: str = HOST, port: int = PORT) -> None:
        self.sock = socket.create_connection((host, port))

    def close(self) -> None:
        self.sock.shutdown(socket.SHUT_RDWR)
        self.sock.close()

    def _call(self, opcode: int, xml: str = "") -> str:
        body = xml.encode("utf-8") if xml else b""
        logging.info("RPC request", 
        extra={"opcode": opcode, "size": len(body), "xml": xml})
        self.sock.sendall(struct.pack("<IH", len(body), opcode) + body)

        resp_opcode, size = struct.unpack("<HI", recv_exact(self.sock, 6))
        resp_xml = recv_exact(self.sock, size).decode("utf-8")
        if resp_opcode != opcode:
            raise ValueError("Opcode missmatch")
        return resp_xml
    def get_entities(self) -> list[tuple]:
        return _rows_from_xml(self._call(OP_GET_ENTITIES))

    def get_queries(self) -> list[tuple]:
        return _rows_from_xml(self._call(OP_GET_QUERIES))

    def get_feedbacks(self) -> list[tuple]:
        return _rows_from_xml(self._call(OP_GET_FEEDBACKS))

    def new_entity(self, *, identifier: int) -> None:
        self._call(OP_NEW_ENTITY, _xml_from_fields(identifier=identifier))

    def new_query(
        self,
        *,
        identifier: int,
        parameter: str,
        entity: int,
        description: str,
        tags: str,
        status: str,
    ) -> None:
        self._call(
            OP_NEW_QUERY,
            _xml_from_fields(
                identifier=identifier,
                parameter=parameter,
                entity=entity,
                description=description,
                tags=tags,
                status=status,
            ),
        )

    def new_feedback(
        self,
        *,
        identifier: int,
        response: str,
        status: str,
        failure: str,
        query: int,
    ) -> None:
        self._call(
            OP_NEW_FEEDBACK,
            _xml_from_fields(
                identifier=identifier,
                response=response,
                status=status,
                failure=failure,
                query=query,
            ),
        )

    def edit_entity(
        self,
        *,
        identifier: int,
        datetime: int | None = None,
        ip: str | None = None,
        locale: str | None = None,
        platform: str | None = None,
    ) -> None:
        self._call(
            OP_EDIT_ENTITY,
            _xml_from_fields(
                identifier=identifier,
                datetime=datetime,
                ip=ip,
                locale=locale,
                platform=platform,
            ),
        )

    def edit_query(
        self,
        *,
        identifier: int,
        datetime: int | None = None,
        parameter: str | None = None,
        entity: int | None = None,
        description: str | None = None,
        tags: str | None = None,
        status: str | None = None,
    ) -> None:
        self._call(
            OP_EDIT_QUERY,
            _xml_from_fields(
                identifier=identifier,
                datetime=datetime,
                parameter=parameter,
                entity=entity,
                description=description,
                tags=tags,
                status=status,
            ),
        )

    def edit_feedback(
        self,
        *,
        identifier: int,
        datetime: int | None = None,
        response: str | None = None,
        status: str | None = None,
        failure: str | None = None,
        query: int | None = None,
    ) -> None:
        self._call(
            OP_EDIT_FEEDBACK,
            _xml_from_fields(
                identifier=identifier,
                datetime=datetime,
                response=response,
                status=status,
                failure=failure,
                query=query,
            ),
        )

    def del_entity(self, identifier: int) -> None:
        self._call(OP_DEL_ENTITY, _xml_from_fields(identifier=identifier))

    def del_query(self, identifier: int) -> None:
        self._call(OP_DEL_QUERY, _xml_from_fields(identifier=identifier))

    def del_feedback(self, identifier: int) -> None:
        self._call(OP_DEL_FEEDBACK, _xml_from_fields(identifier=identifier))

def _xml_from_fields(**fields) -> str:
    root = et.Element("body")
    for name, value in fields.items():
        if value is None:
            continue
        el = et.SubElement(root, name)
        el.text = str(value)
    return et.tostring(root, encoding="unicode")

def _rows_from_xml(xml: str) -> list[tuple]:
    if not xml:
        return []
    root = et.fromstring(xml)
    rows = []
    for row in root.findall("row"):
        values = []
        for child in list(row):
            text = child.text or ""
            values.append(int(text) if text.isdigit() else text)
        rows.append(tuple(values))
    return rows

