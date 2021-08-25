import os
import socket
from sys import argv

from utils.constants import SERVER_ID
from utils.constants import MAX_CHUNK_SIZE

from utils.common import type_encoder
from utils.common import recv_ok_message
from utils.common import initialize_client

from utils.common import send_flw_message
from utils.common import send_msg_message
from utils.common import send_creq_message
from utils.common import send_file_message
from utils.common import send_file_chunk_message

seq_number = 1

# Recuperando o caminho para o diretório atual.
# Todos os arquivos enviados deverão estar na pasta enviar/
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

def get_message_body(message_type, message_tokens):
    """ Função para recuperar a mensagem codificada em ASCII """

    if message_tokens[0] in ('FLW', 'CREQ'):
        return None

    message_body = ' '.join(message_tokens[2:])
    if not message_body.isascii():
        raise ValueError("< your message doesn't contain only ASCII characters, please try again")

    if message_type == 'FILE' and message_body not in os.listdir('enviar/'):
        raise ValueError('< file {} not found in "enviar/" folder'.format(message_body))

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
    message_body = get_message_body(message_type, message_tokens)

    return message_type, dest_id, message_body

def chunkfy(filename):
    """ Função para criar chunks e retornar a extensão (em ASCII) do arquivo multimídia de entrada """
    
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

def run_client(sock, client_id):
    """
        Função principal para implementarmos a lógica do cliente emissor.
        Para desconectar o cliente podemos enviar um FLW via interface ou pressionar CTRL + C.
    """

    global seq_number

    file_id = 0
    while True:
        try:
            buffer = input('> ')
            message_type, dest_id, message_body = parse_typed_message(buffer)
        except ValueError as e:
            print(e)
            continue
        except Exception as e:
            print('< captured exception: {}'.format(e))
            print('< disconnecting from server due to unexpected message format...')
            break

        # Interrompendo o loop para finalizarmos o cliente
        if message_type == 'FLW':
            print('< disconnecting from server...')
            break

        elif message_type == 'MSG':
            message_body = message_body.encode('ascii')
            send_msg_message(sock, client_id, dest_id, seq_number, message_body)
            
            if recv_ok_message(sock, (type_encoder['OK'], SERVER_ID, client_id, seq_number)):
                print('< message MSG sent successfully')
                seq_number += 1
            else:
                print('< an error has occured, please try again')
        
        elif message_type == 'CREQ':
            send_creq_message(sock, client_id, dest_id, seq_number)
            
            if recv_ok_message(sock, (type_encoder['OK'], SERVER_ID, client_id, seq_number)):
                print('< message CREQ sent successfully')
                seq_number += 1
            else:
                print('< an error has occured, please try again')

        elif message_type == 'FILE':
            file_ext, chunks = chunkfy(message_body)
            send_file_message(sock, client_id, dest_id, seq_number, file_id, len(chunks), file_ext)

            if recv_ok_message(sock, (type_encoder['OK'], SERVER_ID, client_id, seq_number)):
                print('< message FILE sent successfully')
                seq_number += 1
            else:
                print('< an error has occured, please try again')
                continue

            # Começando envio de chunks
            for chunk_id, chunk in enumerate(chunks):
                send_file_chunk_message(sock, client_id, dest_id, seq_number, file_id, chunk_id, chunk)

                # Esperando OK do servidor
                if recv_ok_message(sock, (type_encoder['OK'], SERVER_ID, client_id, seq_number)):
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
    source_id = int(argv[2]) if len(argv) == 3 else 1

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        client_id = initialize_client(sock, ip, host, source_id)

        print('< All messages must be in ASCII format (watch out for special characters)')
        print('< All files must exist in the "enviar/" folder')
        print('< Here is the following list of available commands:')
        print('    1. FLW: disconnects from server')
        print('    2. MSG <id> <message>: sends a message to the client specified by the <id> parameter')
        print('    3. CREQ <id>: sends a client list requisition to the client specified by the <id> parameter')
        print('    4. FILE <id> <filename.ext>: sends a file to the client specified by the <id> parameter\n')
        
        # Executando o cliente inicializado
        try:
            run_client(sock, client_id)
        except KeyboardInterrupt:
            print('\n< disconnecting from server...')

        # Enviando mensagem de FLW e esperando um OK do servidor
        send_flw_message(sock, client_id, SERVER_ID, seq_number)
        if recv_ok_message(sock, (type_encoder['OK'], SERVER_ID, client_id, seq_number)):
            print('< Goodbye!')
        else:
            print('< an unexpected error has occured :(')