import socket
import select
from sys import argv
from struct import unpack

from utils.constants import SERVER_ID
from utils.common import recv_expected_length
from utils.common import is_sender, is_displayer
from utils.common import type_encoder, type_decoder
from utils.message_validation import validate_oi_message

from utils.message_creation import send_ok_message
from utils.message_creation import send_erro_message
from utils.message_creation import send_flw_message
from utils.message_creation import send_msg_message
from utils.message_creation import send_clist_message
from utils.message_creation import send_file_message
from utils.message_creation import send_file_chunk_message

# Criaremos um dicionário para mantermos os sockets disponíveis
# Cada chave (socket) terá como informação o id do socket associado
available_sockets = {}

# Também teremos dois dicionários para facilitar a recuperação das associações,
# possibilitando a recuperação do socket e cliente associado (se tivermos).
# Iremos assumir que sempre teremos uma associação 1 para 1.
senders = {}
displayers = {}

# Contadores para podermos criar emissores e exibidores com IDs diferentes
# Iremos ter um conjunto com os possíveis IDs, realizando "pops" para escolhermos um ID
# e "pushes" para inserir novamente um ID que não será mais usado (podendo assim ser escolhido novamente)
sender_ids = set(range(1, 2**12))
displayer_ids = set(range(2**12, 2**13))

def create_client(sock):
    """
        Função auxiliar para criarmos um novo cliente.
        Essa função irá enviar um OK ou um ERRO para o cliente.
    """

    conn, addr = sock.accept()
    print('< received connection from:', addr)

    # Esperamos receber uma mensagem OI para estabelecer conexão
    header = recv_expected_length(conn, 8)
    message_type, source_id, dest_id, seq_number = unpack('!4H', header)

    # Verificando se temos identificadores disponíveis para esse cliente
    if (source_id == 0 and len(displayer_ids) == 0) or (source_id != 0 and len(sender_ids) == 0):
        print('< unique identifiers not available, this server is full')
        send_erro_message(conn, SERVER_ID, source_id, seq_number)
        return

    if type_decoder[message_type] == 'OI':
        status = validate_oi_message(source_id, dest_id, displayers)
        if status == 0:
            client_id = displayer_ids.pop()
            available_sockets[conn] = client_id
            displayers[client_id] = {'sock': conn, 'sender_id': None}

            print('< creating new displayer with ID {}'.format(client_id))
            send_ok_message(conn, SERVER_ID, client_id, seq_number)
            return

        elif status == 1:
            client_id = sender_ids.pop()
            available_sockets[conn] = client_id
            senders[client_id] = {'sock': conn, 'displayer_id': None}
            print('< creating new sender with ID {}'.format(client_id))
            
            if is_displayer(source_id):
                senders[client_id]['displayer_id'] = source_id
                displayers[source_id]['sender_id'] = client_id
                print('< establishing association with displayer {}'.format(source_id))
            
            send_ok_message(conn, SERVER_ID, client_id, seq_number)
            return

    print('< error during client creation')
    send_erro_message(conn, SERVER_ID, source_id, seq_number)

def process_displayer(client_id):
    """
        Função para implementarmos a lógica dos exibidores. Trataremos apenas de mensagens FLW,
        já que essa é a única mensagem que pode ser enviada pelo exibidor fora uma mensagem de
        OK e ERRO (que já são tratadas).
    """

    sock = displayers[client_id]['sock']
    sender_id = displayers[client_id]['sender_id']

    header = recv_expected_length(sock, 8)
    message_type, source_id, dest_id, seq_number = unpack('!4H', header)

    # Verificando se a mensagem recebida é de fato do cliente
    if source_id != client_id:
        print('< [{}] received message from another client'.format(client_id))
        send_erro_message(sock, SERVER_ID, client_id, seq_number)
        return

    if type_decoder[message_type] == 'FLW':
        # Verificando se a mensagem não foi direcionada para o servidor
        if dest_id != SERVER_ID:
            print('< FLW message not directed to server')
            send_erro_message(sock, SERVER_ID, client_id, seq_number)
            return

        # Removendo exibidor e atualizando dicionários
        displayers.pop(client_id)
        available_sockets.pop(sock)
        if sender_id is not None:
            senders[sender_id]['displayer_id'] = None
        
        # Possibilitando com que o identificador seja reutilizado e enviando OK para cliente
        displayer_ids.add(client_id)
        send_ok_message(sock, SERVER_ID, client_id, seq_number)
        print('< [{}] displayer disconnected'.format(client_id))
        return

    # Enviando uma mensagem de erro (default)
    send_erro_message(sock, SERVER_ID, client_id, seq_number)

def process_sender_flw_message(sock, client_id, dest_id, seq_number, displayer_id):
    """ 
        Função para processarmos uma mensagem de FLW.
        Retornaremos True quando recebermos um OK e False caso contrário.
    """

    # Verificando se a mensagem não foi direcionada para o servidor
    if dest_id != SERVER_ID:
        print('< FLW message not directed to server')
        return False

    # Verificando se temos um exibidor associado, se sim devemos removê-lo
    if displayer_id is not None:
        displayer_sock = displayers[displayer_id]['sock']
        send_flw_message(displayer_sock, SERVER_ID, displayer_id, seq_number)

        # Esperando receber um OK do cliente
        header = recv_expected_length(displayer_sock, 8)
        header = unpack('!4H', header)

        if header == (type_encoder['OK'], displayer_id, SERVER_ID, seq_number):
            displayers.pop(displayer_id)
            available_sockets.pop(displayer_sock)

            # Possibilitando com que o identificador seja reutilizado
            displayer_ids.add(displayer_id)
            print('< [{}] displayer {} disconnected'.format(client_id, displayer_id))
        else:
            print('< [{}] an unexpected error has occured :('.format(client_id))
            return False

    # Removendo o emissor e atualizando os dicionários
    senders.pop(client_id)
    available_sockets.pop(sock)

    # Possibilitando com que o identificador seja reutilizado
    sender_ids.add(client_id)
    print('< [{}] sender disconnected'.format(client_id))

    return True

def process_sender_msg_message(sock, client_id, dest_id, seq_number):
    # Lendo a mensagem propriamente dita
    message_length = unpack('!H', recv_expected_length(sock, 2))[0]
    message_body = recv_expected_length(sock, message_length)
    
    # Verificando se a mensagem será de broadcast
    if dest_id == 0:
        for displayer_id in displayers:
            # Enviando mensagem para o exibidor
            displayer_sock = displayers[displayer_id]['sock']
            send_msg_message(displayer_sock, client_id, displayer_id, seq_number, message_body)

            # Esperando por uma mensagem de OK
            header = recv_expected_length(displayer_sock, 8)
            header = unpack('!4H', header)

            if header == (type_encoder['OK'], displayer_id, SERVER_ID, seq_number):
                print('< [{}] message sent to displayer {}'.format(client_id, displayer_id))
            else:
                print('< [{}] an unexpected error has occured :('.format(client_id))
                return False
        
        return True

    elif is_sender(dest_id):
        if dest_id not in senders:
            print('< [{}] client trying to send message to non-existent sender'.format(client_id))
            return False

        displayer_id = senders[dest_id]['displayer_id']
        if displayer_id is None:
            print('< [{}] client trying to send message to sender with no displayer'.format(client_id))
            return False
        
        # Enviando mensagem para exibidor e esperando um OK
        displayer_sock = displayers[displayer_id]['sock']
        send_msg_message(displayer_sock, client_id, displayer_id, seq_number, message_body)
        
        header = recv_expected_length(displayer_sock, 8)
        header = unpack('!4H', header)

        if header == (type_encoder['OK'], displayer_id, SERVER_ID, seq_number):
            print('< [{}] message sent to sender {} with displayer {}'.format(client_id, dest_id, displayer_id))
            return True
        else:
            print('< [{}] an unexpected error has occured :('.format(client_id))
            return False
    
    elif is_displayer(dest_id):
        if dest_id not in displayers:
            print('< [{}] client trying to send message to non-existent displayer'.format(client_id))
            return False

        # Enviando mensagem para exibidor e esperando um OK
        displayer_sock = displayers[dest_id]['sock']
        send_msg_message(displayer_sock, client_id, dest_id, seq_number, message_body)
        
        header = recv_expected_length(displayer_sock, 8)
        header = unpack('!4H', header)

        if header == (type_encoder['OK'], dest_id, SERVER_ID, seq_number):
            print('< [{}] message sent to displayer {}'.format(client_id, dest_id))
            return True
        else:
            print('< [{}] an unexpected error has occured :('.format(client_id))
            return False

    print("< [{}] the client didn't inform a valid receiver ID".format(client_id))
    return False

def process_sender_creq_message(sock, client_id, dest_id, seq_number):
    # Construindo a lista de clientes
    client_list = [*senders] + [*displayers]

    # Verificando se a mensagem será de broadcast
    if dest_id == 0:
        for displayer_id in displayers:
            # Enviando mensagem para o exibidor
            displayer_sock = displayers[displayer_id]['sock']
            send_clist_message(displayer_sock, client_id, displayer_id, seq_number, client_list)

            # Esperando por uma mensagem de OK
            header = recv_expected_length(displayer_sock, 8)
            header = unpack('!4H', header)

            if header == (type_encoder['OK'], displayer_id, SERVER_ID, seq_number):
                print('< [{}] message sent to displayer {}'.format(client_id, displayer_id))
            else:
                print('< [{}] an unexpected error has occured :('.format(client_id))
                return False
        
        return True

    elif is_sender(dest_id):
        if dest_id not in senders:
            print('< [{}] client trying to send message to non-existent sender'.format(client_id))
            return False

        displayer_id = senders[dest_id]['displayer_id']
        if displayer_id is None:
            print('< [{}] client trying to send message to sender with no displayer'.format(client_id))
            return False
        
        # Enviando mensagem para exibidor e esperando um OK
        displayer_sock = displayers[displayer_id]['sock']
        send_clist_message(displayer_sock, client_id, displayer_id, seq_number, client_list)
        
        header = recv_expected_length(displayer_sock, 8)
        header = unpack('!4H', header)

        if header == (type_encoder['OK'], displayer_id, SERVER_ID, seq_number):
            print('< [{}] message sent to sender {} with displayer {}'.format(client_id, dest_id, displayer_id))
            return True
        else:
            print('< [{}] an unexpected error has occured :('.format(client_id))
            return False
    
    elif is_displayer(dest_id):
        if dest_id not in displayers:
            print('< [{}] client trying to send message to non-existent displayer'.format(client_id))
            return False

        # Enviando mensagem para exibidor e esperando um OK
        displayer_sock = displayers[dest_id]['sock']
        send_clist_message(displayer_sock, client_id, dest_id, seq_number, client_list)
        
        header = recv_expected_length(displayer_sock, 8)
        header = unpack('!4H', header)

        if header == (type_encoder['OK'], dest_id, SERVER_ID, seq_number):
            print('< [{}] message sent to displayer {}'.format(client_id, dest_id))
            return True
        else:
            print('< [{}] an unexpected error has occured :('.format(client_id))
            return False

    print("< [{}] the client didn't inform a valid receiver ID".format(client_id))
    return False

def process_sender_file_message(sock, client_id, dest_id, seq_number):
    # Lendo metadados da mensagem
    file_id, n_chunks, len_ext = unpack('!3H', recv_expected_length(sock, 6))
    file_ext = recv_expected_length(sock, len_ext)
 
    # Verificando se a mensagem será de broadcast
    if dest_id == 0:
        for displayer_id in displayers:
            # Repassando a mensagem FILE para o exibidor e esperando um OK
            displayer_sock = displayers[displayer_id]['sock']
            send_file_message(displayer_sock, client_id, displayer_id, seq_number, file_id, n_chunks, file_ext)
            
            header = recv_expected_length(displayer_sock, 8)
            header = unpack('!4H', header)

            if header == (type_encoder['OK'], displayer_id, SERVER_ID, seq_number):
                print('< [{}] message sent to sender {} with displayer {}'.format(client_id, dest_id, displayer_id))
            else:
                print('< [{}] an unexpected error has occured :('.format(client_id))
                send_erro_message(sock, SERVER_ID, client_id, seq_number)
                return

        # Enviando OK para emissor começar a enviar FILE_CHUNK
        send_ok_message(sock, SERVER_ID, client_id, seq_number)

        # Iremos repassar N chunks do emissor para os exibidores
        for _ in range(n_chunks):
            # Lendo cabeçalho apenas para recuperarmos o número de sequência
            chunk_header = recv_expected_length(sock, 8)
            _, _, _, seq_number = unpack('!4H', chunk_header)

            # Lendo os metadados para recuperarmos o tamanho do chunk
            chunk_metadata = recv_expected_length(sock, 6)
            file_id, chunk_id, len_chunk = unpack('!3H', chunk_metadata)
            chunk = recv_expected_length(sock, len_chunk)

            for displayer_id in displayers:
                # Repassando chunk e esperando um OK do exibidor
                displayer_sock = displayers[displayer_id]['sock']
                send_file_chunk_message(displayer_sock, client_id, displayer_id, seq_number, file_id, chunk_id, chunk)

                header = recv_expected_length(displayer_sock, 8)
                header = unpack('!4H', header)

                if header == (type_encoder['OK'], displayer_id, SERVER_ID, seq_number):
                    print('< [{}] message sent to sender {} with displayer {}'.format(client_id, dest_id, displayer_id))
                else:
                    print('< [{}] an unexpected error has occured :('.format(client_id))
                    send_erro_message(sock, SERVER_ID, client_id, seq_number)
                    return

            # Enviando OK para emissor começar a enviar o próximo FILE_CHUNK
            send_ok_message(sock, SERVER_ID, client_id, seq_number)

    elif is_sender(dest_id):
        if dest_id not in senders:
            print('< [{}] client trying to send message to non-existent sender'.format(client_id))
            send_erro_message(sock, SERVER_ID, client_id, seq_number)
            return

        displayer_id = senders[dest_id]['displayer_id']
        if displayer_id is None:
            print('< [{}] client trying to send message to sender with no displayer'.format(client_id))
            send_erro_message(sock, SERVER_ID, client_id, seq_number)
            return

        # Repassando a mensagem FILE para o exibidor e esperando um OK para iniciarmos
        # a troca de mensagens do tipo FILE_CHUNK
        displayer_sock = displayers[displayer_id]['sock']
        send_file_message(displayer_sock, client_id, displayer_id, seq_number, file_id, n_chunks, file_ext)
        
        header = recv_expected_length(displayer_sock, 8)
        header = unpack('!4H', header)

        if header == (type_encoder['OK'], displayer_id, SERVER_ID, seq_number):
            print('< [{}] message sent to sender {} with displayer {}'.format(client_id, dest_id, displayer_id))
            send_ok_message(sock, SERVER_ID, client_id, seq_number)
        else:
            print('< [{}] an unexpected error has occured :('.format(client_id))
            send_erro_message(sock, SERVER_ID, client_id, seq_number)
            return

        # Iremos repassar N chunks do emissor para o exibidor
        for _ in range(n_chunks):
            # Lendo cabeçalho apenas para recuperarmos o número de sequência
            chunk_header = recv_expected_length(sock, 8)
            _, _, _, seq_number = unpack('!4H', chunk_header)

            # Lendo os metadados para recuperarmos o tamanho do chunk
            chunk_metadata = recv_expected_length(sock, 6)
            file_id, chunk_id, len_chunk = unpack('!3H', chunk_metadata)
            chunk = recv_expected_length(sock, len_chunk)

            # Repassando chunk e esperando um OK do exibidor
            send_file_chunk_message(displayer_sock, client_id, displayer_id, seq_number, file_id, chunk_id, chunk)

            header = recv_expected_length(displayer_sock, 8)
            header = unpack('!4H', header)

            if header == (type_encoder['OK'], displayer_id, SERVER_ID, seq_number):
                print('< [{}] message sent to sender {} with displayer {}'.format(client_id, dest_id, displayer_id))
                send_ok_message(sock, SERVER_ID, client_id, seq_number)
            else:
                print('< [{}] an unexpected error has occured :('.format(client_id))
                send_erro_message(sock, SERVER_ID, client_id, seq_number)
                return

    elif is_displayer(dest_id):
        if dest_id not in displayers:
            print('< [{}] client trying to send message to non-existent displayer'.format(client_id))
            send_erro_message(sock, SERVER_ID, client_id, seq_number)
            return

        # Repassando a mensagem FILE para o exibidor e esperando um OK para iniciarmos
        # a troca de mensagens do tipo FILE_CHUNK
        displayer_id = dest_id
        displayer_sock = displayers[displayer_id]['sock']
        send_file_message(displayer_sock, client_id, displayer_id, seq_number, file_id, n_chunks, file_ext)
        
        header = recv_expected_length(displayer_sock, 8)
        header = unpack('!4H', header)

        if header == (type_encoder['OK'], displayer_id, SERVER_ID, seq_number):
            print('< [{}] message sent to sender {} with displayer {}'.format(client_id, dest_id, displayer_id))
            send_ok_message(sock, SERVER_ID, client_id, seq_number)
        else:
            print('< [{}] an unexpected error has occured :('.format(client_id))
            send_erro_message(sock, SERVER_ID, client_id, seq_number)
            return

        # Iremos repassar N chunks do emissor para o exibidor
        for _ in range(n_chunks):
            # Lendo cabeçalho apenas para recuperarmos o número de sequência
            chunk_header = recv_expected_length(sock, 8)
            _, _, _, seq_number = unpack('!4H', chunk_header)

            # Lendo os metadados para recuperarmos o tamanho do chunk
            chunk_metadata = recv_expected_length(sock, 6)
            file_id, chunk_id, len_chunk = unpack('!3H', chunk_metadata)
            chunk = recv_expected_length(sock, len_chunk)

            # Repassando chunk e esperando um OK do exibidor
            send_file_chunk_message(displayer_sock, client_id, displayer_id, seq_number, file_id, chunk_id, chunk)

            header = recv_expected_length(displayer_sock, 8)
            header = unpack('!4H', header)

            if header == (type_encoder['OK'], displayer_id, SERVER_ID, seq_number):
                print('< [{}] message sent to sender {} with displayer {}'.format(client_id, dest_id, displayer_id))
                send_ok_message(sock, SERVER_ID, client_id, seq_number)
            else:
                print('< [{}] an unexpected error has occured :('.format(client_id))
                send_erro_message(sock, SERVER_ID, client_id, seq_number)
                return

    else:
        print("< [{}] the client didn't inform a valid receiver ID".format(client_id))
        send_erro_message(sock, SERVER_ID, client_id, seq_number)

def process_sender(client_id):
    """ Função para implementarmos a lógica dos emissores. """

    sock = senders[client_id]['sock']
    displayer_id = senders[client_id]['displayer_id']

    header = recv_expected_length(sock, 8)
    message_type, source_id, dest_id, seq_number = unpack('!4H', header)

    # Verificando se a mensagem recebida é de fato do cliente
    if source_id != client_id:
        print('< [{}] received message from another client'.format(client_id))
        send_erro_message(sock, SERVER_ID, client_id, seq_number)
        return

    if type_decoder[message_type] == 'FLW':
        response_header = [sock, SERVER_ID, client_id, seq_number]
        success = process_sender_flw_message(sock, client_id, dest_id, seq_number, displayer_id)
        send_ok_message(*response_header) if success else send_erro_message(*response_header)

    elif type_decoder[message_type] == 'MSG':
        response_header = [sock, SERVER_ID, client_id, seq_number]
        success = process_sender_msg_message(sock, client_id, dest_id, seq_number)
        send_ok_message(*response_header) if success else send_erro_message(*response_header)

    elif type_decoder[message_type] == 'CREQ':
        response_header = [sock, SERVER_ID, client_id, seq_number]
        success = process_sender_creq_message(sock, client_id, dest_id, seq_number)
        send_ok_message(*response_header) if success else send_erro_message(*response_header)

    elif type_decoder[message_type] == 'FILE':
        process_sender_file_message(sock, client_id, dest_id, seq_number)

    else:
        # Enviando uma mensagem de erro (default)
        send_erro_message(sock, SERVER_ID, client_id, seq_number)
    
if __name__ == '__main__':
    if len(argv) != 2:
        print('usage: {} <port>'.format(argv[0]))
        exit(1)

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as mysock:
        mysock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        mysock.bind(('', int(argv[1])))
        mysock.listen()

        # Inserindo o socket do servidor nos sockets disponíveis
        available_sockets[mysock] = SERVER_ID

        print('< running on:', mysock.getsockname())
        print('< waiting for connections...')

        while True:
            ready_sockets, _, _ = select.select(available_sockets.keys(), [], [])
            for sock in ready_sockets:
                if available_sockets[sock] == SERVER_ID:
                    create_client(sock)

                elif is_sender(available_sockets[sock]):
                    process_sender(available_sockets[sock])

                elif is_displayer(available_sockets[sock]):
                    process_displayer(available_sockets[sock])

                else:
                    print('< socket not recognized as server or client')
                
                print('-----------------------------------\n')
                print('--> socket ids:', available_sockets)
                print('--> emissores:', senders)
                print('--> exibidores:', displayers)
                print('\n-----------------------------------')