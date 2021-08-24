from struct import unpack

from .constants import BUFSZ

type_encoder = {
    'OK': 1, 'ERRO': 2, 'OI': 3,
    'FLW': 4, 'MSG': 5, 'CREQ': 6,
    'CLIST': 7, 'FILE': 8, 'FILE_CHUNK': 9
}

type_decoder = {value:key for key, value in type_encoder.items()}

def recv_expected_length(sock, expected_length):
    """
        Método auxiliar para lermos uma quantidade esperada de bytes de um recv.
        O método pode gerar uma excessão ``RuntimeError`` indicando um erro na comunicação.
    """

    buffer = b''
    bytes_received = 0

    while bytes_received < expected_length:            
        data = sock.recv(min(expected_length - bytes_received, BUFSZ))
        if not data:
            raise RuntimeError('connection terminated unexpectedly')

        buffer += data
        bytes_received = bytes_received + len(data)

    return buffer

def is_sender(id):
    return id >= 1 and id <= (2**12 - 1)

def is_displayer(id):
    return id >= 2**12 and id <= (2**13 - 1)