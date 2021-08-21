import sys
import socket
from sys import argv
from struct import pack, unpack

from utils.common import recv_expected_length
from utils.common import type_encoder, type_decoder
from utils.constants import HEADER_FMT, HEADER_SIZE, SERVER_ID

client_counter = 1

if __name__ == '__main__':
    if len(argv) != 2:
        print('usage: {} <porto>'.format(argv[0]))
        sys.exit(1)

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind(('', int(argv[1])))
        sock.listen()

        print('< servidor definido em:', sock.getsockname())

        while True:
            conn, addr = sock.accept()
            print('< recebi conexão do endereço:', addr)

            # Lendo o cabeçalho da mensagem
            buffer = recv_expected_length(conn, HEADER_SIZE)
            header = unpack(HEADER_FMT, buffer)
            print(header)

            # Verificando o tipo de mensagem e tratando de acordo
            type = type_decoder[header[0]]
            if type == 'OI':
                if header[1] == 0:
                    print('< devo inicializar um exibidor')
                else:
                    print('< devo inicializar um emissor')
                    
                    if header[1] >= 2**12 and header[1] <= 2**13-1:
                        print('< e ele terá um exibidor associado')

                # Por enquanto iremos sempre mandar um OK
                msg = pack(HEADER_FMT, type_encoder['OK'], SERVER_ID, client_counter, 0)
                conn.sendall(msg)

                client_counter += 1