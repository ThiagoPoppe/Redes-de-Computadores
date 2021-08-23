import socket
import threading
from sys import argv
from struct import unpack

from utils.constants import SERVER_ID
from utils.common import recv_expected_length
from utils.common import is_displayer, type_decoder, type_encoder

from utils.message_creation import send_ok_message
from utils.message_creation import send_erro_message
from utils.message_creation import send_flw_message

from utils.message_validation import validate_oi_message

senders = {}
displayers = {}

sender_count = 1
displayer_count = 2**12

thread_lock = threading.Lock()

# TODO: criar função check_for_ok com expected_header

def sender_thread(sock, client_id):
    while True:
        thread_lock.acquire()

        header = recv_expected_length(sock, 8)
        message_type, source_id, dest_id, seq_number = unpack('!4H', header)

        # Verificando se a mensagem recebida é de fato do cliente
        if source_id != client_id:
            print('< [{}] received message from another client'.format(client_id))
            send_erro_message(sock, SERVER_ID, client_id, seq_number)
            continue

        # Caso a mensagem seja um FLW, iremos desconectar o emissor
        # e um exibidor associado (se existir)
        if type_decoder[message_type] == 'FLW':
            if dest_id != SERVER_ID:
                send_erro_message(sock, SERVER_ID, client_id, seq_number)
                continue

            # Caso onde não temos um exibidor associado
            elem = senders[client_id]
            if elem['displayer_id'] is None:
                senders.pop(client_id)
                print('< [{}] client disconnected'.format(client_id))
                send_ok_message(sock, SERVER_ID, client_id, seq_number)
                thread_lock.release()
                break
            
            # Caso tivermos um exibidor associado devemos então remover ele primeiro!
            else:
                displayer_id = elem['displayer_id']
                displayer_sock = displayers[displayer_id]
                send_flw_message(displayer_sock, SERVER_ID, displayer_id, seq_number)

                # Esperando por um OK do exibidor
                header = recv_expected_length(displayer_sock, 8)
                header = unpack('!4H', header)

                if header == (type_encoder['OK'], displayer_id, SERVER_ID, seq_number):
                    displayers.pop(displayer_id)
                    senders.pop(client_id)
                    print('< [{}] disconnecting displayer {}'.format(client_id, elem['displayer_id']))
                    print('< [{}] client disconnected'.format(client_id))
                    send_ok_message(sock, SERVER_ID, client_id, seq_number)
                    thread_lock.release()
                    break
                else:
                    print('< [{}] something went wrong :('.format(client_id))
                    send_erro_message(sock, SERVER_ID, client_id, seq_number)
        
        thread_lock.release()

if __name__ == '__main__':
    if len(argv) != 2:
        print('usage: {} <port>'.format(argv[0]))
        exit(1)

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind(('', int(argv[1])))
        sock.listen()

        print('< running on:', sock.getsockname())
        while True:
            print('< waiting for connections...')
            conn, addr = sock.accept()
            print('< received connection from:', addr)

            # Variáveis para salvarmos o ID do cliente e o seu tipo
            client_id = -1
            client_type = None

            # Esperamos receber uma mensagem OI para estabelecer conexão
            header = recv_expected_length(conn, 8)
            header = unpack('!4H', header)

            if type_decoder[header[0]] == 'OI':
                status = validate_oi_message(header[1], header[2], displayers)
                if status == 0:
                    client_type = 'displayer'
                    client_id = displayer_count
                    displayers[displayer_count] = conn

                    send_ok_message(conn, SERVER_ID, displayer_count, header[3])
                    displayer_count += 1

                elif status == 1:
                    client_type = 'sender'
                    client_id = sender_count
                    senders[sender_count] = {
                        'sock': conn,
                        'displayer_id': header[1] if is_displayer(header[1]) else None
                    }

                    send_ok_message(conn, SERVER_ID, sender_count, header[3])                    
                    sender_count += 1
                
                else:
                    send_erro_message(conn, SERVER_ID, header[1], header[3])
                    continue
            else:
                send_erro_message(conn, SERVER_ID, header[1], header[3])
                continue

            # print('emissores:', senders)
            # print('exibidores:', displayers)

            # Disparando uma thread para o emissor criado
            # Note que não há necessidade de criarmos uma thread para o exibidor
            if client_type == 'sender':
                thread = threading.Thread(target=sender_thread, args=(conn, client_id))
                thread.start()