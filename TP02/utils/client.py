import socket
from struct import unpack

from utils import constants
from utils.base import BaseNode

class Client(BaseNode):
    """ Classe para modelar a ponta ativa da comunicação. """

    def __init__(self, ip, host, input_file, output_file):
        super().__init__(input_file, output_file)
        
        # Conectando com o servidor (ponta passiva)
        self.socket.connect((ip, int(host)))

    def run(self):
        # print('Devemos enviar {} quadros'.format(len(self.send_frames)))

        # Laço para enviarmos e receber alguns dados da outra ponta
        while True:
            # Enviando o quadro de dados atual
            # print('enviando quadro', self.send_idx)
            self.send_data_frame(self.socket)

            # Recebendo algo da outra ponta
            try:
                frame = self.search_frame(self.socket, self.last_chksum, self.last_id)
            except socket.timeout:
                # print('timeout!')
                continue
            except RuntimeError:
                # print('erro na conexão, encerrando...')
                self.close_node = True
                break

            # Verificando se conseguimos encontrar um quadro válido
            if frame is None:
                continue
            
            # Extraíndo o cabeçalho do quadro recebido
            header = unpack(constants.HEADER_FORMAT, frame[:14])
            # print('recebi quadro com header:', header)

            # Verificando se recebemos um quadro de confirmação
            if header[5] == 0x80 and (self.send_idx % 2) == header[4]:
                # print('recebi um ACK do quadro {}, mandando próximo quadro'.format(self.send_idx))
                
                # Se estamos no último quadro (END) não iremos mais mandar dados
                self.send_idx += 1
                if self.send_idx == len(self.send_frames):
                    # print('recebi meu ACK do END')
                    break

            # Verificando se recebemos um quadro duplicado
            elif header[3] == self.last_chksum and header[4] == self.last_id:
                # print('recebemos um quadro duplicado! enviando ack')
                self.send_ack_frame(self.socket, self.last_id)

            # Se nenhuma condição for satisfeita, então teremos um quadro com dados!
            else:
                # Caso o id seja igual (i.e quadro repetido) mas com checksum diferente
                # significa que recebemos um quadro com algum erro!
                if header[3] != self.last_chksum and header[4] == self.last_id:
                    continue

                # Iremos salvar o quadro e enviar um quadro de confirmação
                self.last_chksum, self.last_id = header[3], header[4]
                self.recv_frames.append(frame)

                # print('recebi dado... enviando ack!')
                self.send_ack_frame(self.socket, header[4])

        # Executando loop para verificar se precisamos receber mais alguma coisa
        while not self.close_node:
            try:
                frame = self.search_frame(self.socket, self.last_chksum, self.last_id)
            except socket.timeout:
                # print('timeout, posso finalizar!')
                self.close_node = True
                continue
            except RuntimeError:
                # print('erro na conexão, encerrando...')
                break

            # Verificando se conseguimos encontrar um quadro válido
            if frame is None:
                continue

            # Extraíndo o cabeçalho do quadro recebido
            header = unpack(constants.HEADER_FORMAT, frame[:14])

            # Caso recebermos um quadro de ACK podemos desconsiderar
            # uma vez que já enviamos todos os dados necessários.
            if header[5] == 0x80:
                continue

            # Verificando se recebemos um quadro duplicado
            elif header[3] == self.last_chksum and header[4] == self.last_id:
                # print('recebemos um quadro duplicado! enviando ack')
                # print(header)
                self.send_ack_frame(self.socket, self.last_id)

            # Se nenhuma condição for satisfeita, então teremos um quadro com dados!
            # Iremos salvar o quadro e enviar um quadro de confirmação
            else:
                # Caso o id seja igual (i.e quadro repetido) mas com checksum diferente
                # significa que recebemos um quadro com algum erro!
                if header[3] != self.last_chksum and header[4] == self.last_id:
                    continue

                self.last_chksum, self.last_id = header[3], header[4]
                self.recv_frames.append(frame)

                # print('enviando ack!')
                self.send_ack_frame(self.socket, header[4])

        # Escrevendo os dados recebidos pela outra ponta e encerrando
        with open(self.output_file, 'wb') as outfile:
            data = b''.join([frame[14:] for frame in self.recv_frames])
            outfile.write(data)