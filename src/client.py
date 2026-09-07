import socket

sock = socket.create_connection(("localhost", 8000))

def get_entities():
    return socket.call(opcode=1)