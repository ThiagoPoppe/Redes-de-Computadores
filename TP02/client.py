import socket
from sys import argv

from utils import encode16

send_data = '110111001100000000100011110000101101110011000000001000111100001000000000000001001111101011101111000000000000000000000001000000100000001100000100'

#######
## Sending data
# 1) Encode each header part
# 2) Pack everything and send

## Receiving
# 3) Unpack data
# 4) Decode each header part
#######

if __name__ == '__main__':
    if len(argv) != 6:
        print('usage: python {} -c <IP> <port> <input> <output>'.format(argv[0]))
        exit(1)

    ip, port = argv[2], argv[3]
    infile, outfile = argv[4], argv[5]

    sync = send_data[:32]
    print('SYNC:', send_data[:32], len(sync), 'bits')
    print('SYNC:', encode16(send_data[:32]))

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((ip, int(port)))

        print('Original send data =', send_data)
        print('Encoded send data =', encode16(send_data))

        s.sendall(encode16(send_data).encode())