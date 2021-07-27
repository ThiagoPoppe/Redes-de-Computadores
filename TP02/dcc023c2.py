from os import sync
import time
import sys
import socket
import select

from struct import pack, unpack
from base64 import b16decode as decode16
from base64 import b16encode as encode16

# TODO: Implementar computação do checksum e trocar quando define um frame

BUFSZ = 2**16
MAX_LENGTH = 2**16 - 1

SYNC = 0xdcc023c2
SYNC_BYTES = pack('!I', SYNC)

def send_encoded_message(sock, send_buffer):
    sock.sendall(encode16(send_buffer))

def send_end_frame(sock):
    print('Enviando frame de END')
    frame = [SYNC, SYNC, 0, 0, 0, 0x40]
    frame = pack('!IIHHBB', *frame)
    send_encoded_message(sock, frame)

def send_ack_frame(sock, id_):
    print('Enviando frame de ACK')
    frame = [SYNC, SYNC, 0, 0, id_, 0x80]
    frame = pack('!IIHHBB', *frame)
    send_encoded_message(sock, frame)

def receive_decoded_message(sock, timeout=1.0):
    ready = select.select([sock], [], [], timeout)
    if not ready[0]:
        return None
    
    buffer = decode16(sock.recv(BUFSZ))
    sync_pos = buffer.find(2 * SYNC_BYTES)

    # Procurando pela sequência de sincronização
    while sync_pos == -1:
        buffer = decode16(sock.recv(BUFSZ))
        if not buffer: # não achamos
            return None

        sync_pos = buffer.find(2 * SYNC_BYTES)

    # Recuperando começo do quadro e cabeçalho
    buffer = buffer[sync_pos:]
    header = unpack('!IIHHBB', buffer[:14])

    # Iremos ler dados até atingirmos o esperado
    while len(buffer[14:]) < header[2]:
        data = sock.recv(BUFSZ)
        if not data: # não temos mais nada para ler (provável erro no length)
            return None

        buffer += decode16(data)

    # Computando tamanho do quadro e retornando
    frame_length = 14 + header[2]
    return buffer[:frame_length]

def run_client(ip, host, infile, outfile):
    with open(infile, 'rb') as fin:
        input_data = fin.read()

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.connect((ip, int(host)))

        n_frames = 1 + (len(input_data) // MAX_LENGTH)
        print('Devo mandar {} frames'.format(n_frames))

        # Loop principal para enviar input
        i = 0
        while i < n_frames:
            print('Enviando frame {}'.format(i))

            # Obtendo os próximos bytes a ser enviados
            send_buffer = input_data[:MAX_LENGTH]

            frame = [SYNC, SYNC, len(send_buffer), 0, i%2, 0x3f, send_buffer]
            frame = pack('!IIHHBB{}s'.format(len(send_buffer)), *frame)
            send_encoded_message(sock, frame)

            # Apenas continuamos a mandar dados se recebemos um ACK!
            recv_buffer = receive_decoded_message(sock, 1.0)
            if recv_buffer is None:
                print('Ocorreu timeout ou algum erro de transmissão')
                continue

            header = unpack('!IIHHBB', recv_buffer[:14])
            if header[5] == 0x80:
                print('RECEBI ACK!')
                # Avançando o ponteiro dos dados de entrada
                i += 1
                input_data = input_data[MAX_LENGTH:]
    
        # Terminando a conexão
        send_end_frame(sock)

def run_server(host, infile, outfile):
    last_id = 1
    output_data = b''
    done_receiving_data = False

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind(('', int(host)))
        sock.listen()

        conn, addr = sock.accept()
        print('connected by:', addr)

        while not done_receiving_data:
            recv_buffer = receive_decoded_message(conn)
            if recv_buffer is None:
                print('Ocorreu timeout ou algum erro de transmissão')
                continue
            
            sync1, sync2, length, chksum, id_, flags = unpack('!IIHHBB', recv_buffer[:14])
            if flags == 0x40:
                print('Encerrando transmissão')
                done_receiving_data = True
                break
            
            # Recebemos quadros com id diferente do último quadro
            elif id_ != last_id:
                output_data += recv_buffer[14:14+length].replace(2*SYNC_BYTES, b'')
                last_id = id_
                
                send_ack_frame(conn, id_)

    with open(outfile, 'wb') as fout:
        fout.write(output_data) 

if __name__ == '__main__':
    if sys.argv[1] == '-s':
        run_server(*sys.argv[2:])

    elif sys.argv[1] == '-c':
        run_client(*sys.argv[2:])