import sys
import socket
from sys import argv
from struct import pack, unpack

from utils.common import recv_expected_length
from utils.common import type_encoder, type_decoder
from utils.constants import HEADER_FMT, HEADER_SIZE, INITIAL_SENDER_ID, SERVER_ID

if __name__ == '__main__':
    if len(argv) != 2 and len(argv) != 3:
        print('usage: {} <IP:porto> [exibidor]'.format(argv[0]))
        sys.exit(1)

    ip, host = argv[1].split(':')
    exhibitor = int(argv[2]) if len(argv) == 3 else None

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.connect((ip, int(host)))

        # Loop para enviarmos a primeira mensagem "OI"
        while True:
            buffer = input('> ')
            if buffer != 'OI':
                print('< a primeira mensagem deve ser um OI')
                continue
            
            # Construindo e enviando a mensagem de OI
            source_id = exhibitor if exhibitor is not None else INITIAL_SENDER_ID
            msg = pack(HEADER_FMT, type_encoder[buffer], source_id, SERVER_ID, 0)
            sock.sendall(msg)

            # Recebendo uma confirmação do servidor
            buffer = recv_expected_length(sock, HEADER_SIZE)
            fields = unpack(HEADER_FMT, buffer)

            type = type_decoder[fields[0]]
            if type == 'OK':
                client_id = int(fields[2])
                print('< o seu id será', client_id)
                break

            elif type == 'ERRO':
                print('< ocorreu um erro, envie a mensagem novamente')

        print('Opa blz, bora começar')