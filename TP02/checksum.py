from struct import pack
from base64 import b16encode as encode16
from base64 import b16decode as decode16

from utils.common import compute_checksum, verify_frame_integrity

SYNC = 0xdcc023c2

if __name__ == '__main__':
    ###### PRIMEIRO EXEMPLO DO MONITOR ######
    data = b'Teste123'
    correct_frame = b'dcc023c2dcc023c200089fb300005465737465313233'.upper()

    header = [SYNC, SYNC, len(data), 0, 0, 0]
    header = pack('!IIHHBB', *header)
    frame = compute_checksum(header + data)

    encoded_frame = encode16(frame)
    if encoded_frame == correct_frame:
        print('EXEMPLO 1 está idêntico')

    decoded_frame = decode16(encoded_frame)
    if verify_frame_integrity(decoded_frame):
        print('Verify deu certo!')

    print()
    print()

    ###### SEGUNDO EXEMPLO DO MONITOR ######
    data = b'mensagem de teste'
    correct_frame = b'dcc023c2dcc023c2001189dc00006d656e736167656d206465207465737465'.upper()

    header = [SYNC, SYNC, len(data), 0, 0, 0]
    header = pack('!IIHHBB', *header)
    frame = compute_checksum(header + data)

    encoded_frame = encode16(frame)
    if encoded_frame == correct_frame:
        print('EXEMPLO 2 está idêntico')

    decoded_frame = decode16(encoded_frame)
    if verify_frame_integrity(decoded_frame):
        print('Verify deu certo!')