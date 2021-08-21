from .constants import BUFSZ

type_encoder = {
    'OK': 1, 'ERRO': 2, 'OI': 3,
    'FLW': 4, 'MSG': 5, 'CREQ': 6,
    'CLIST': 7, 'FILE': 8, 'FILE_CHUNK': 9
}

type_decoder = {
    1: 'OK', 2: 'ERRO', 3: 'OI',
    4: 'FLW', 5: 'MSG', 6: 'CREQ',
    7: 'CLIST', 8: 'FILE', 9: 'FILE_CHUNK'
}

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
            raise RuntimeError()

        buffer += data
        bytes_received = bytes_received + len(data)

    return buffer

def get_message_type(type):
    if type == 'OK':
        return 1
    if type == 'ERRO':
        return 2
    if type == 'OI':
        return 3
    if type == 'FLW':
        return 4
    if type == 'MSG':
        return 5
    if type == 'CREQ':
        return 6
    if type == 'CLIST':
        return 7
    if type == 'FILE':
        return 8
    if type == 'FILE_CHUNK':
        return 9