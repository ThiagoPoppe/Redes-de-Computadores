import socket
import select
from struct import pack, unpack
from base64 import b16encode as encode16
from base64 import b16decode as decode16

from utils import constants

class BaseNode:
    """
        Essa classe será usada para definir comportamentos similares tanto para
        a ponta ativa quanto para a ponta passiva.
    """

    def __init__(self, input_file, output_file):
        # Criando quadros de envio
        with open(input_file, 'rb') as infile:
            self.send_frames = self.create_frames(infile.read())

        # Definindo lista de quadros de saída
        self.recv_frames = []
        self.output_file = output_file

        # Variáveis de controle para o envio e recebimento dos quadros
        self.send_idx = 0
        self.last_id = 1
        self.last_chksum = -1

        # Variáveis de controle para comunicação
        self.close_node = False
        
        # Criando socket
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    def __del__(self):
        self.socket.close()

    def create_frames(self, data):
        """
            Método auxiliar para criarmos os quadros com os dados de envio.
            Esse método também irá criar o quadro de END, marcando o fim da comunicação.
        """

        # Computando quantos quadros são necessários para o envio completo dos dados
        n_frames = (len(data) // constants.MAX_LENGTH)
        if len(data) % constants.MAX_LENGTH != 0:
            n_frames += 1
        
        frames = []
        for i in range(n_frames):
            begin = i * constants.MAX_LENGTH
            end = begin + constants.MAX_LENGTH

            buffer = data[begin:end]
            header = [constants.SYNC, constants.SYNC, len(buffer), 0, (i%2), 0]
            print(header)
            
            frame = pack(constants.HEADER_FORMAT, *header) + buffer
            frame = self.fill_checksum_field(frame)
            frames.append(frame)

        # Criando o quadro de END que demarca o fim de comunicação
        header = [constants.SYNC, constants.SYNC, 0, 0, (i+1)%2, 0x40]
        print(header)
        frame = pack(constants.HEADER_FORMAT, *header)
        frame = self.fill_checksum_field(frame)
        frames.append(frame)

        return frames

    def compute_checksum(self, frame):
        """ Método auxiliar para computar o checksum de um quadro """

        # Usaremos um frame auxiliar para computar o checksum
        # Se o quadro tiver tamanho ímpar nós precisamos inserir um byte 0 no final
        aux_frame = frame
        if len(frame) % 2 != 0:
            aux_frame += b'\x00'

        # Somando 2 em 2 bytes
        chksum = 0
        for i in range(0, len(aux_frame), 2):
            chksum += int.from_bytes(aux_frame[i:i+2], byteorder='big')

        # Tratando de carry on
        while (chksum >> 16) != 0:
            chksum = (chksum >> 16) + (chksum & 0xffff)

        # Retornando o valor do checksum
        return ~chksum & 0xffff

    def fill_checksum_field(self, frame):
        """ 
            Método para preencher o campo checksum de um quadro, 
            retornando o quadro completo.
        """

        chksum = self.compute_checksum(frame)
        return frame[:10] + pack('!H', chksum) + frame[12:]

    def verify_frame_integrity(self, frame):
        """ Método para verificar a integridade do quadro (campo checksum). """

        return self.compute_checksum(frame) == 0

    def send_data_frame(self, sock):
        """ Método auxiliar para enviarmos um quadro de dados para a rede. """

        frame = self.send_frames[self.send_idx]
        sock.sendall(encode16(frame))

    def send_ack_frame(self, sock, id):
        """ Método para criar e enviar um quadro ACK para a rede """

        frame = [constants.SYNC, constants.SYNC, 0, 0, id, 0x80]
        frame = pack(constants.HEADER_FORMAT, *frame)
        frame = self.fill_checksum_field(frame)

        sock.sendall(encode16(frame))

    def recv_expected_length(self, sock, expected_length, timeout=1.0):
        """
            Método auxiliar para lermos uma quantidade esperada de bytes (em base16)
            de um recv. Esse método irá retornar os bytes decodificados, ou seja,
            aplicando decode16.

            O método pode gerar uma excessão ``socket.timeout`` ou ``RuntimeError`` indicando
            um timeout no recv e um erro na comunicação, respectivamente.
        """

        buffer = b''
        bytes_received = 0

        while bytes_received < expected_length:
            # Iremos esperar 1 segundo até dar timeout
            ready = select.select([sock], [], [], timeout)
            if not ready[0]:
                raise socket.timeout()
                
            data = sock.recv(min(expected_length - bytes_received, constants.BUFSZ))
            if not data:
                raise RuntimeError()

            buffer += data
            bytes_received = bytes_received + len(data)

        return decode16(buffer)

    def search_frame(self, sock, last_chksum, last_id):
        """
            Método que irá procurar e retornar um quadro válido.

            Caso isso não seja possível, devido à algum erro presente no quadro,
            iremos retornar None.
        """

        # Procurando uma sequência de sincronização
        # Em base16 a sequência terá 2*8 = 16 bytes
        header = self.recv_expected_length(sock, 16)
        while header != constants.SYNC_BYTES:
            print(header)
            input()
            header = self.recv_expected_length(sock, 16)

        print('\nencontrei começo do quadro!')

        # Obtendo restante do cabeçalho do quadro
        # Em base16 o restante do cabeçalho terá 2*6 = 12 bytes
        header += self.recv_expected_length(sock, 12)
        header = unpack(constants.HEADER_FORMAT, header)

        # Caso o campo id não seja 0 ou 1 teremos um erro
        if header[4] not in (0, 1):
            print('campo id incorreto!')
            return None

        # Caso o campo flag não seja 0x00, 0x40 ou 0x80 teremos um erro
        if header[5] not in (0x00, 0x40, 0x80):
            print('campo flag incorreto!')
            return None

        # Caso o campo length seja diferente de 0 mas temos um ACK ou END
        # significa que recebemos um quadro errado!
        if header[2] != 0 and (header[5] == 0x80 or header[5] == 0x40):
            print('campo length incorreto!')
            return None

        # Caso o campo length seja 0 mas não temos um ACK ou END
        # significa que recebemos um quadro errado!
        if header[2] == 0 and (header[5] != 0x40 and header[5] != 0x80):
            print('campo de length incorreto!')
            return None

        # Obtendo os dados do quadro
        # Em base16 teremos 2*length bytes de dados
        data = self.recv_expected_length(sock, 2*header[2])

        # Verificando integridade do quadro
        frame = pack(constants.HEADER_FORMAT, *header) + data
        if self.verify_frame_integrity(frame) == False:
            print('checksum inválido!')
            return None

        return frame

    def run(self):
        """ Método para executar a lógica principal de comunicação. """

        raise NotImplementedError()