import socket
import socketserver
import struct
import xml.etree.ElementTree as et

import models

HOST = "localhost"
PORT = 8001

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

ENTITY_FIELDS = ("identifier", "datetime", "ip", "locale", "platform")
QUERY_FIELDS = (
    "identifier",
    "datetime",
    "parameter",
    "entity",
    "description",
    "tags",
    "status",
)
FEEDBACK_FIELDS = (
    "identifier",
    "datetime",
    "response",
    "status",
    "failure",
    "query",
)
INT_FIELDS = {"identifier", "datetime", "entity", "query"}


def recv_exact(sock: socket.socket, n: int) -> bytes:
    buff = b""
    while len(buff) < n:
        chunk = sock.recv(n - len(buff))
        if not chunk:
            raise ConnectionError("Client closed connection")
        buff += chunk
    return buff


def fields_from_xml(xml: str) -> dict:
    if not xml:
        return {}
    root = et.fromstring(xml)
    result = {}
    for child in list(root):
        text = child.text or ""
        if child.tag in INT_FIELDS:
            result[child.tag] = int(float(text))
        else:
            result[child.tag] = text
    return result


def rows_to_xml(rows: list[tuple], field_names: tuple[str, ...]) -> str:
    root = et.Element("body")
    for row in rows:
        node = et.SubElement(root, "row")
        for name, value in zip(field_names, row):
            el = et.SubElement(node, name)
            el.text = str(value)
    return et.tostring(root, encoding="unicode")


def dispatch(opcode: int, xml: str) -> str:
    fields = fields_from_xml(xml)
    if opcode == OP_GET_ENTITIES:
        return rows_to_xml(models.get_entities(), ENTITY_FIELDS)
    if opcode == OP_GET_QUERIES:
        return rows_to_xml(models.get_queries(), QUERY_FIELDS)
    if opcode == OP_GET_FEEDBACKS:
        return rows_to_xml(models.get_feedbacks(), FEEDBACK_FIELDS)
    if opcode == OP_NEW_ENTITY:
        models.new_entity(**fields)
        return ""
    if opcode == OP_NEW_QUERY:
        models.new_query(**fields)
        return ""
    if opcode == OP_NEW_FEEDBACK:
        models.new_feedback(**fields)
        return ""
    if opcode == OP_EDIT_ENTITY:
        models.edit_entity(**fields)
        return ""
    if opcode == OP_EDIT_QUERY:
        models.edit_query(**fields)
        return ""
    if opcode == OP_EDIT_FEEDBACK:
        models.edit_feedback(**fields)
        return ""
    if opcode == OP_DEL_ENTITY:
        models.del_entity(fields["identifier"])
        return ""
    if opcode == OP_DEL_QUERY:
        models.del_query(fields["identifier"])
        return ""
    if opcode == OP_DEL_FEEDBACK:
        models.del_feedback(fields["identifier"])
        return ""
    raise ValueError(f"Unknown opcode {opcode}")


class RpcHandler(socketserver.BaseRequestHandler):
    def handle(self) -> None:
        while True:
            try:
                header = recv_exact(self.request, 6)
                size, opcode = struct.unpack("<IH", header)
                raw = recv_exact(self.request, size) if size else b""
                xml = raw.decode("utf-8")
                try:
                    resp_xml = dispatch(opcode, xml)
                except Exception as exc:
                    resp_xml = (
                        f"<body><error>{exc}</error></body>"
                    )
                body = resp_xml.encode("utf-8") if resp_xml else b""
                reply = struct.pack("<HI", opcode, len(body))
                self.request.sendall(reply + body)
            except ConnectionError:
                break


class RpcServer(socketserver.ThreadingTCPServer):
    allow_reuse_address = True


if __name__ == "__main__":
    with RpcServer((HOST, PORT), RpcHandler) as server:
        print(f"RPC server on {HOST}:{PORT}")
        server.serve_forever()
