import socket
from sys import argv
from struct import unpack

from utils.constants import SERVER_ID

from utils.common import recv_expected_length
from utils.common import type_encoder, type_decoder

from utils.message_creation import send_oi_message
from utils.message_creation import send_flw_message
from utils.message_creation import send_msg_message
from utils.message_creation import send_creq_message
from utils.message_creation import send_file_message

seq_number = 0

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

    return message_body.encode('ascii')

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

    if message_type not in ('FLW', 'MSG', 'CREQ', 'FILE'):
        raise ValueError('< message type must be FLW, MSG, CREQ or FILE')
    elif message_type == 'FLW' and len(message_tokens) != 1:
        raise ValueError('< the FLW message does not contain any additional parameters, please try again')
    elif message_type == 'CREQ' and len(message_tokens) != 2:
        raise ValueError("< the CREQ message only requires the receiver's ID as parameter, please try again")
    elif (message_type == 'MSG' or message_type == 'FILE') and len(message_tokens) < 3:
        raise ValueError('< not enough parameters specified, please try again')

    dest_id = get_dest_id(message_tokens)
    message_body = get_message_body(message_tokens)

    return message_type, dest_id, message_body

def run_client(sock, source_id):
    """
        Função principal para implementarmos a lógica do cliente emissor.
        Para desconectar o cliente podemos enviar um FLW via interface ou pressionar CTRL + C.
    """

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
                print('\< an unexpected error has occured :(')

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