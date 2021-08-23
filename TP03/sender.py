import socket
from sys import argv
from struct import unpack

from utils.constants import SERVER_ID
from utils.common import type_encoder, type_decoder
from utils.common import recv_expected_length
from utils.message_creation import send_oi_message
from utils.message_creation import send_flw_message
from utils.message_creation import send_msg_message
from utils.message_creation import send_creq_message
from utils.message_creation import send_file_message

if __name__ == '__main__':
    if len(argv) not in (2, 3):
        print('usage: {} <IP:port> [displayer]'.format(argv[0]))
        exit(1)

    seq_number = 0
    ip, host = argv[1].split(':')

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.connect((ip, int(host)))

        # Enviando mensagem de OI para conectar ao servidor
        source_id = int(argv[2]) if len(argv) == 3 else 1
        send_oi_message(sock, source_id, seq_number)

        # Verificando se recebemos um OK do servidor
        header = recv_expected_length(sock, 8)
        header = unpack('!4H', header)

        if type_decoder[header[0]] == 'OK':
            seq_number += 1
            source_id = header[2]
            print('< your id is:', source_id)
        else:
            print('< something went wrong... Please try again')
            exit(1)

        # Loop principal para lermos mensagens do emissor
        supported_messages = ('FLW', 'MSG', 'CREQ', 'FILE')
        while True:
            buffer = input('> ')
            type = buffer.split(' ')[0]

            if type not in supported_messages:
                print('< message type must be one of the following:', supported_messages)
                continue

            # Enviando mensagem de FLW e esperando resposta do servidor
            if type == 'FLW':
                send_flw_message(sock, source_id, SERVER_ID, seq_number)

                header = recv_expected_length(sock, 8)
                header = unpack('!4H', header)

                if header == (type_encoder['OK'], SERVER_ID, source_id, seq_number):
                    print('< disconnecting from server... Goodbye!')
                    break
                else:
                    print('< something went wrong... Please try again!')