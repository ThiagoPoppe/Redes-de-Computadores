import socket
from sys import argv
from struct import unpack

from utils.constants import SERVER_ID

from utils.common import recv_expected_length
from utils.common import type_encoder, type_decoder

from utils.message_creation import send_oi_message
from utils.message_creation import send_flw_message
from utils.message_creation import send_ok_message

seq_number = 0

def run_client(sock, source_id):
    """
        Função principal para implementarmos a lógica do cliente exibidor.
        Para desconectar o cliente podemos pressionar CTRL + C.
    """

    while True:
        header = recv_expected_length(sock, 8)
        header = unpack('!4H', header)

        # Caso recebermos um FLW devemos encerrar a conexão
        if type_decoder[header[0]] == 'FLW':
            send_ok_message(sock, source_id, SERVER_ID, seq_number)
            print('< closing displayer... Goodbye!')
            break
        
        print('< received header:', header)

if __name__ == '__main__':
    if len(argv) != 2:
        print('usage: {} <IP:port>'.format(argv[0]))
        exit(1)

    ip, host = argv[1].split(':')
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.connect((ip, int(host)))

        # Enviando mensagem de OI para conectar ao servidor
        send_oi_message(sock, 0, seq_number)

        # Verificando se recebemos um OK do servidor
        header = recv_expected_length(sock, 8)
        header = unpack('!4H', header)

        if type_decoder[header[0]] == 'OK':
            seq_number += 1
            source_id = header[2]
            print('< Welcome, client! Your id is:', source_id)
        else:
            print('< something went wrong, please try again')
            exit(1)

        try:
            run_client(sock, source_id)
        except KeyboardInterrupt:
            # Enviando mensagem de FLW e esperando resposta do servidor
            send_flw_message(sock, source_id, SERVER_ID, seq_number)

            header = recv_expected_length(sock, 8)
            header = unpack('!4H', header)
            if header == (type_encoder['OK'], SERVER_ID, source_id, seq_number):
                print('\n< closing displayer... Goodbye!')
            else:
                print('\n< an unexpected error has occured :(')