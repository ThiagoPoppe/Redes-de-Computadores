import os
import socket
from sys import argv
from struct import unpack

from utils.constants import SERVER_ID
from utils.common import type_encoder, type_decoder

from utils.common import recv_ok_message
from utils.common import initialize_client
from utils.common import recv_expected_length

from utils.common import send_ok_message
from utils.common import send_flw_message

# Recuperando o caminho para o diretório atual.
# Iremos salvar todos os arquivos recebidos na pasta recebidos/
workdir = os.path.dirname(os.path.abspath(__file__))
savedir = os.path.join(workdir, 'recebidos')

def recv_file_chunks(sock, client_id, n_chunks):
    """ Função para recuperarmos a lista de chunks do arquivo """

    chunks = []
    for _ in range(n_chunks):
        # Lendo cabeçalho apenas para recuperarmos o número de sequência
        header = recv_expected_length(sock, 8)
        _, _, _, seq_number = unpack('!4H', header)

        # Lendo os metadados para recuperarmos o tamanho do chunk
        _, _, len_chunk = unpack('!3H', recv_expected_length(sock, 6))
        chunk = recv_expected_length(sock, len_chunk)

        # Armazenando chunk e enviando OK
        chunks.append(chunk)
        send_ok_message(sock, client_id, SERVER_ID, seq_number)
    
    return chunks

def run_client(sock, client_id):
    """
        Função principal para implementarmos a lógica do cliente exibidor.
        Para desconectar o cliente podemos pressionar CTRL + C.
    """

    while True:
        header = recv_expected_length(sock, 8)
        message_type, source_id, _, seq_number = unpack('!4H', header)

        if type_decoder[message_type] == 'FLW':
            send_ok_message(sock, client_id, SERVER_ID, seq_number)
            print('< closing displayer... Goodbye!')
            break

        elif type_decoder[message_type] == 'MSG':
            # Lendo a mensagem propriamente dita
            message_length = unpack('!H', recv_expected_length(sock, 2))[0]
            message_body = recv_expected_length(sock, message_length)
            
            print('< MSG from {}: {}'.format(source_id, message_body.decode('ascii')))
            send_ok_message(sock, client_id, SERVER_ID, seq_number)

        elif type_decoder[message_type] == 'CLIST':
            # Lendo a lista de clientes
            n_clients = unpack('!H', recv_expected_length(sock, 2))[0]
            client_list = recv_expected_length(sock, 2 * n_clients)

            fmt = '!{}H'.format(n_clients)
            client_list = unpack(fmt, client_list)

            print('< client list:', client_list)
            send_ok_message(sock, client_id, SERVER_ID, seq_number)

        elif type_decoder[message_type] == 'FILE':
            # Lendo metadados da mensagem
            file_id, n_chunks, len_ext = unpack('!3H', recv_expected_length(sock, 6))
            file_ext = recv_expected_length(sock, len_ext)
            file_ext = file_ext.decode('ascii')

            # Enviando um OK para o servidor e recuperando cada chunk
            send_ok_message(sock, client_id, SERVER_ID, seq_number)
            chunks = recv_file_chunks(sock, client_id, n_chunks)

            # Salvando arquivo no formato IdExibidor_IdEmissor_IdArquivo.EXT
            filename = '{}_{}_{}.{}'.format(client_id, source_id, file_id, file_ext)
            filename = os.path.join(savedir, filename)
            print('< received FILE from {}: {}'.format(source_id, filename))

            with open(filename, 'wb') as fout:
                data = b''.join([chunk for chunk in chunks])
                fout.write(data)
            
if __name__ == '__main__':
    if len(argv) != 2:
        print('usage: {} <IP:port>'.format(argv[0]))
        exit(1)

    seq_number = 1
    ip, host = argv[1].split(':')
    
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        client_id = initialize_client(sock, ip, host, source_id=0)
        
        try:
            run_client(sock, client_id)
        except KeyboardInterrupt:
            # Enviando mensagem de FLW e esperando resposta do servidor
            send_flw_message(sock, client_id, SERVER_ID, seq_number)
            if recv_ok_message(sock, (type_encoder['OK'], SERVER_ID, client_id, seq_number)):
                print('\n< closing displayer... Goodbye!')
            else:
                print('\n< an unexpected error has occured :(')