import socket
from sys import argv
from base64 import b16encode as encode16
from base64 import b16decode as decode16

def run_client(ip, host, infile, outfile):
    with open(infile, 'rb') as fin:
        send_data = fin.read()

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((ip, int(host)))

        encoded_data = encode16(send_data)
        print('Original sent data:', send_data)
        print('Encoded sent data :', encoded_data)

        s.sendall(encoded_data)

def run_server(host, infile, outfile):
    buffer = b''
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind(('', int(host)))
        s.listen()

        conn, addr = s.accept()
        with conn:
            print('connected by:', addr)
            while True:
                recv_data = conn.recv(8192)
                if not recv_data:
                    break

                decoded_data = decode16(recv_data)
                print('Original received data:', recv_data)
                print('Decoded received data :', decoded_data)
                
                buffer += decoded_data

    with open(outfile, 'wb') as fout:
        fout.write(buffer)

if __name__ == '__main__':
    if argv[1] == '-s':
        try:
            run_server(*argv[2:])
        except Exception:
            print('usage: python {} -s <port> <input> <output>'.format(argv[0]))
            exit(1)

    elif argv[1] == '-c':
        try:
            run_client(*argv[2:])
        except Exception:
            print('usage: python {} -c <ip> <port> <input> <output>'.format(argv[0]))
            exit(1)