import socket
import select
from struct import pack, unpack
from base64 import b16encode as encode16
from base64 import b16decode as decode16

from utils import constants

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