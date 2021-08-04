import random
import socket
from struct import unpack

from utils import constants
from utils.common import create_frames
from utils.common import send_ack_frame
from utils.common import send_encoded_frame
from utils.common import recv_decoded_frame

class Client:
    def __init__(self, ip, host, input_file, output_file):
        # Criando quadros de envio
        with open(input_file, 'rb') as infile:
            self.send_frames = create_frames(infile.read())

        # Definindo lista de quadros de saída
        self.recv_frames = []
        self.output_file = output_file
        
        # Criando o socket do cliente
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.connect((ip, int(host)))

    def __del__(self):
        self.socket.close()

    def run(self):
        send_idx = 0
        last_id = 1
        last_chksum = -1
        print('Tenho que mandar {} frames'.format(len(self.send_frames)))
        while send_idx < len(self.send_frames):
            print('\nEnviando quadro', send_idx)

            to_send = bytearray(self.send_frames[send_idx])

            coin = random.uniform(0,1)
            if coin < 0.5:
                print('enviaremos o quadro com:')

                coin = random.uniform(0,1)
                if coin < 0.05:
                    print('erro no SYNC!')
                    to_send[0:1] = b'\xff'
                
                if coin < 0.15:
                    print('erro no length')
                    to_send[8:10] = b'\x04\x08'
                
                if coin < 0.25:
                    print('erro no checksum!')
                    to_send[10:12] = b'\x04\x08'
                
                if coin < 0.5:
                    print('erro no id')
                    to_send[12:13] = b'\x02'
                
                if coin < 0.75:
                    print('erro no flag')
                    to_send[13:14] = b'\xfa'

                if coin <= 1:
                    print('erro nos dados')
                    to_send[14:16] = b'\x04\x08'
            
            input()
            send_encoded_frame(self.socket, to_send)

            try:
                frame = recv_decoded_frame(self.socket, last_chksum, last_id)
            except socket.timeout:
                print('timeout!')
                continue
            except RuntimeError:
                print('erro na conexão, encerrando...')
                break
            
            # Verificamos se conseguimos ler um quadro válido
            if frame is None:
                continue

            header = unpack(constants.HEADER_FORMAT, frame[:14])

            # Verificando se recebemos um quadro duplicado
            if header[3] == last_chksum and header[4] == last_id:
                print('recebemos um quadro duplicado!')
                send_ack_frame(self.socket, last_id)
                continue

            # Verificando se recebemos um quadro de confirmação
            if header[5] == 0x80 and (send_idx % 2) == header[4]:
                print('recebi um ack do quadro {}, mandando próximo quadro'.format(send_idx))
                send_idx += 1

            last_chksum, last_id = header[3], header[4]