import socket
import select
from struct import pack, unpack
from base64 import b16encode as encode16
from base64 import b16decode as decode16

from utils import constants

# TODO: CRIAR ANOMALIAS NOS QUADROS

def compute_checksum(frame):
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
    
    # Inserindo checksum no quadro
    frame = bytearray(frame)
    frame[10:12] = pack('!H', (~chksum) & 0xffff)

    return frame

def verify_frame_integrity(frame):
    # Usaremos um frame auxiliar para computar o checksum
    # Se o quadro tiver tamanho ímpar nós precisamos inserir um byte 0 no final
    aux_frame = frame
    if len(frame) % 2 != 0:
        aux_frame += b'\x00'

    # Somando 2 em 2 bytes
    verify = 0
    for i in range(0, len(aux_frame), 2):
        verify += int.from_bytes(aux_frame[i:i+2], byteorder='big')

    # Tratando de carry on
    while (verify >> 16) != 0:
        verify = (verify >> 16) + (verify & 0xffff)
    
    # Caso o complemento de 1 seja 0 nós temos um quadro válido
    return (~verify & 0xffff) == 0

def send_encoded_frame(sock, frame):
    sock.sendall(encode16(frame))

def send_ack_frame(sock, id):
    frame = [constants.SYNC, constants.SYNC, 0, 0, id, 0x80]
    frame = pack(constants.HEADER_FORMAT, *frame)
    send_encoded_frame(sock, compute_checksum(frame))

def myrecv(sock, expected_length, timeout=1.0):
    chunks = []
    bytes_received = 0

    while bytes_received < expected_length:
        # Iremos esperar 1 segundo até dar timeout
        ready = select.select([sock], [], [], timeout)
        if not ready[0]:
            raise socket.timeout()
            
        chunk = sock.recv(min(expected_length - bytes_received, constants.BUFSZ))
        if chunk == b'':
            raise RuntimeError()

        chunks.append(chunk)
        bytes_received = bytes_received + len(chunk)

    return b''.join(chunks)

def recv_decoded_frame(sock, last_chksum, last_id):
    # Procurando uma sequência de sincronização
    header = decode16(myrecv(sock, 16))
    while header != constants.SYNC_BYTES:
        header = decode16(myrecv(sock, 16))

    print('\nencontrei começo do quadro!')

    # Obtendo restante do cabeçalho do quadro
    header += decode16(myrecv(sock, 12))
    header = unpack(constants.HEADER_FORMAT, header)

    # Caso o campo id não seja 0 ou 1 teremos um erro
    if header[4] not in (0, 1):
        print('campo id incorreto!')
        return None

    # Caso o id seja igual (i.e quadro repetido) mas com checksum diferente
    # significa que recebemos um quadro com algum erro!
    if header[3] != last_chksum and header[4] == last_id:
        print('quadro repetido com algum erro!')
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
        print(header)
        print('campo de length incorreto!')
        return None

    # Obtendo os dados do quadro
    data = decode16(myrecv(sock, 2*header[2]))

    # Verificando integridade do quadro
    frame = pack(constants.HEADER_FORMAT, *header) + data
    if not verify_frame_integrity(frame):
        print('checksum inválido!')
        return None

    return frame

def create_frames(data):
    n_frames = (len(data) // constants.MAX_LENGTH)
    if len(data) % constants.MAX_LENGTH != 0:
        n_frames += 1
    
    frames = []
    for i in range(n_frames):
        begin = i * constants.MAX_LENGTH
        end = begin + constants.MAX_LENGTH

        buffer = data[begin:end]
        header = [constants.SYNC, constants.SYNC, len(buffer), 0, (i%2), 0]
        
        frame = pack(constants.HEADER_FORMAT, *header) + buffer
        frames.append(compute_checksum(frame))

    # Criando o quadro de END que demarca o fim de comunicação
    header = [constants.SYNC, constants.SYNC, 0, 0, (i+1)%2, 0x40]
    frame = pack(constants.HEADER_FORMAT, *header)
    frames.append(compute_checksum(frame))

    return frames