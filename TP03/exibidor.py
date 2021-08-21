import sys
import socket
from sys import argv

from utils.constants import BUFSZ

if __name__ == '__main__':
    if len(argv) != 2:
        print('usage: {} <IP:porto>'.format(argv[0]))
        sys.exit(1)

    ip, host = argv[1].split(':')

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.connect((ip, int(host)))

        msg = input('> ')
        sock.sendall(msg.encode())

        buf = sock.recv(BUFSZ)
        print('<', buf.decode())