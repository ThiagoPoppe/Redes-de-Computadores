import time
import socket
from struct import unpack

from utils import constants
from utils.common import create_frames
from utils.common import send_ack_frame
from utils.common import recv_decoded_frame

class Server:
    def __init__(self, host, input_file, output_file):
        # Criando quadros de envio
        with open(input_file, 'rb') as infile:
            self.send_frames = create_frames(infile.read())

        # Definindo lista de quadros de saída
        self.recv_frames = []
        self.output_file = output_file

        # Criando o socket do servidor
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.socket.bind(('', int(host)))
        self.socket.listen()

    def __del__(self):
        self.socket.close()

    def run(self):
        conn, addr = self.socket.accept()
        print('connected by:', addr)

        last_id = 1
        last_chksum = -1
        while True:
            try:
                frame = recv_decoded_frame(conn, last_chksum, last_id)
            except socket.timeout:
                print('timeout!')
                continue
            except RuntimeError:
                print('erro na conexão, encerrando...')
                break

            if frame is None:
                continue

            header = unpack(constants.HEADER_FORMAT, frame[:14])

            # Verificando se recebemos um quadro duplicado
            if header[3] == last_chksum and header[4] == last_id:
                print('recebemos um quadro duplicado!')
                send_ack_frame(conn, last_id)
                continue

            # Salvando quadro e enviando quadro de confirmação
            last_chksum, last_id = header[3], header[4]
            self.recv_frames.append(frame)

            print('enviando ack!')
            send_ack_frame(conn, header[4])

        with open(self.output_file, 'wb') as outfile:
            data = b''.join([frame[14:] for frame in self.recv_frames])
            outfile.write(data)