import os
import socket
from sys import argv
from struct import unpack

from utils.constants import SERVER_ID
from utils.constants import MAX_CHUNK_SIZE

from utils.common import recv_expected_length
from utils.common import type_encoder, type_decoder

from utils.message_creation import send_oi_message
from utils.message_creation import send_flw_message
from utils.message_creation import send_msg_message
from utils.message_creation import send_creq_message
from utils.message_creation import send_file_message
from utils.message_creation import send_file_chunk_message

file_id = 0
seq_number = 0

# Recuperando o caminho para o diretório atual.
# Todos os arquivos a ser enviados deverão estar na pasta enviar/
workdir = os.path.dirname(os.path.abspath(__file__))
senddir = os.path.join(workdir, 'enviar')

def get_dest_id(message_tokens):
    """ Função para recuperar o ID do destinatário da mensagem """

    if message_tokens[0] == 'FLW':
        return None

    dest_id = message_tokens[1]
    if not dest_id.isdigit():
        raise ValueError('< {} is not a integer, please try again'.format(dest_id))

    return int(dest_id)

def get_message_body(message_tokens):
    """ Função para recuperar a mensagem codificada em ASCII """

    if message_tokens[0] in ('FLW', 'CREQ'):
        return None

    message_body = ' '.join(message_tokens[2:])
    if not message_body.isascii():
        raise ValueError("< your message doesn't contain only ASCII characters, please try again")

    return message_body

def parse_typed_message(buffer):
    """ 
        Função auxiliar para realizar o parse de mensagens.
        Essa função irá retornar o tipo da mensagem, id de destino e corpo da mensagem (caso exista).
        Note que ela também irá levantar exceções quando tivermos erros de formatação da mensagem!
    """
    
    if len(buffer) == 0:
        raise ValueError('< an empty message is not a valid message, please try again')

    message_tokens = buffer.split()
    message_type = message_tokens[0]

    if message_type == 'FLW' and len(message_tokens) != 1:
        raise ValueError('< the FLW message does not contain any additional parameters, please try again')
    elif message_type == 'CREQ' and len(message_tokens) != 2:
        raise ValueError("< the CREQ message only requires the receiver's ID as parameter, please try again")
    elif (message_type == 'MSG' or message_type == 'FILE') and len(message_tokens) < 3:
        raise ValueError('< not enough parameters specified, please try again')

    dest_id = get_dest_id(message_tokens)
    message_body = get_message_body(message_tokens)

    return message_type, dest_id, message_body

def chunkfy(filename):
    """ Função para criar chunks e retornar a extensão (em ASCII) do arquivo multimídia de entrada """
    
    if not filename.isascii():
        raise ValueError("< your message doesn't contain only ASCII characters, please try again")
    
    # Recuperando a extensão do arquivo e lendo o arquivo em binário
    file_ext = filename.split('.')[1].encode('ascii')    
    with open(os.path.join(senddir, filename), 'rb') as fin:
        data = fin.read()

    # Computando quantos chunks devemos enviar
    n_chunks = (len(data) // MAX_CHUNK_SIZE)
    if len(data) % MAX_CHUNK_SIZE != 0:
        n_chunks += 1

    chunks = []
    for i in range(n_chunks):
        begin = i * MAX_CHUNK_SIZE
        end = begin + MAX_CHUNK_SIZE

        chunk = data[begin:end]
        chunks.append(chunk)

    return file_ext, chunks

def run_client(sock, source_id):
    """
        Função principal para implementarmos a lógica do cliente emissor.
        Para desconectar o cliente podemos enviar um FLW via interface ou pressionar CTRL + C.
    """

    global file_id
    global seq_number

    while True:
        try:
            buffer = input('> ')
            message_type, dest_id, message_body = parse_typed_message(buffer)
        except ValueError as e:
            print(e)
            continue

        # Enviando mensagem de FLW e esperando resposta do servidor
        if message_type == 'FLW':
            send_flw_message(sock, source_id, SERVER_ID, seq_number)

            header = recv_expected_length(sock, 8)
            header = unpack('!4H', header)
            if header == (type_encoder['OK'], SERVER_ID, source_id, seq_number):
                print('< disconnecting from server... Goodbye!')
                break
            else:
                print('< an unexpected error has occured :(')

        elif message_type == 'MSG':
            message_body = message_body.encode('ascii')
            send_msg_message(sock, source_id, dest_id, seq_number, message_body)

            header = recv_expected_length(sock, 8)
            header = unpack('!4H', header)
            if header == (type_encoder['OK'], SERVER_ID, source_id, seq_number):
                print('< message sent successfully')
                seq_number += 1
            else:
                print('< an error has occured, please try again')
        
        elif message_type == 'CREQ':
            send_creq_message(sock, source_id, dest_id, seq_number)

            header = recv_expected_length(sock, 8)
            header = unpack('!4H', header)
            if header == (type_encoder['OK'], SERVER_ID, source_id, seq_number):
                print('< message sent successfully')
                seq_number += 1
            else:
                print('< an error has occured, please try again')

        elif message_type == 'FILE':
            file_ext, chunks = chunkfy(message_body)
            send_file_message(sock, source_id, dest_id, seq_number, file_id, len(chunks), file_ext)

            # Esperando OK do servidor
            header = recv_expected_length(sock, 8)
            header = unpack('!4H', header)
            if header == (type_encoder['OK'], SERVER_ID, source_id, seq_number):
                print('< message sent successfully')
                seq_number += 1
            else:
                print('< an error has occured, please try again')
                continue

            # Começando envio de chunks
            for chunk_id, chunk in enumerate(chunks):
                send_file_chunk_message(sock, source_id, dest_id, seq_number, file_id, chunk_id, chunk)

                # Esperando OK do servidor
                header = recv_expected_length(sock, 8)
                header = unpack('!4H', header)
                if header == (type_encoder['OK'], SERVER_ID, source_id, seq_number):
                    print('< file chunk {} sent successfully'.format(chunk_id))
                    seq_number += 1
                else:
                    print('< an unexpected error has occured :(')

            # Após o arquivo ser enviado por completo, atualizaremos o ID do arquivo
            print('< file {} sent successfully'.format(message_body))
            file_id += 1

        else:
            print('< message type must be FLW, MSG, CREQ or FILE')

if __name__ == '__main__':
    if len(argv) not in (2, 3):
        print('usage: {} <IP:port> [displayer]'.format(argv[0]))
        exit(1)

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
            
            print('< Welcome, client! Your id is:', source_id)
            print('< Here is the following list of available commands:')
            print('    1. FLW: disconnects from server')
            print('    2. MSG <id> <message>: sends a message to the client specified by the <id> parameter')
            print('    3. CREQ <id>: sends a client list requisition to the client specified by the <id> parameter')
            print('    4. FILE <id> <filename.ext>: sends a file to the client specified by the <id> parameter')
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
                print('\n< disconnecting from server... Goodbye!')
            else:
                print('\n< an unexpected error has occured :(')