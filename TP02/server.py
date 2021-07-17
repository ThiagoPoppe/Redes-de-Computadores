import socket
from sys import argv

from utils import decode16

if __name__ == '__main__':
    if len(argv) != 5:
        print('usage: python {} -s <port> <input> <output>'.format(argv[0]))
        exit(1)

    port = int(argv[2])
    infile, outfile = argv[3], argv[4]

    hostname = socket.gethostname()
    local_ip = socket.gethostbyname(hostname)

    recv_data = None

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind((local_ip, port))
        s.listen()
        print('listening at (ip, port) =', (local_ip, port))

        conn, addr = s.accept()
        with conn:
            print('Connected by:', addr)
            while True:
                recv_data = conn.recv(1024)
                if not recv_data:
                    break

                print('Original received data =', recv_data)
                print('Decoded received data =', decode16(recv_data))