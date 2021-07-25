import socket
from sys import argv
from struct import pack, unpack
from base64 import b16encode as encode16, encode
from base64 import b16decode as decode16

####### ESTRUTURA DO PACOTE #######
#
#   SYNC   => 32 bits  = 4 bytes (int -> I)
#   SYNC   => 32 bits  = 4 bytes (int -> I)
#   length => 16 bits  = 2 bytes (unsigned short -> H)
#   chksum => 16 bits  = 2 bytes (unsigned short -> H)
#   ID     =>  8 bits  = 1 byte (unsigned char -> B)
#   flags  =>  8 bits  = 1 byte (unsigned char -> B)
#   dados  => no máximo 2¹⁶-1 bytes (bytes -> s (must pass the number of bytes))
#
###################################

SYNC = 3703579586
MAX_DATA_BYTESIZE = 2**16 - 1

def receive_message(conn):
    """ Helper function to receive a message dealing with multiple recv calls """

    recv_buffer = b''
    while True:
        data = conn.recv(65536)
        if not data:
            break
        
        recv_buffer += data

    return recv_buffer

def run_client(ip, host, infile, outfile):
    with open(infile, 'rb') as fin:
        send_data = fin.read()

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((ip, int(host)))

        length = len(send_data)
        size = length
        chksum = 42
        id_ = 2
        flags = 10

        fmt = 'IIHHBB{}s'.format(length)
        packet = pack(fmt, SYNC, SYNC, length, chksum, id_, flags, send_data)

        s.sendall(encode16(packet))

def run_server(host, infile, outfile):
    buffer = b''
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind(('', int(host)))
        s.listen()

        conn, addr = s.accept()
        with conn:
            print('connected by:', addr)

            recv_buffer = decode16(receive_message(conn))
            header = unpack('IIHHBB', recv_buffer[:14])
            
            print(header)
            buffer = recv_buffer[14:]

    with open(outfile, 'wb') as fout:
        fout.write(buffer)

if __name__ == '__main__':
    if argv[1] == '-s':
        try:
            run_server(*argv[2:])
        except Exception as e:
            print(e)
            print('usage: python {} -s <port> <input> <output>'.format(argv[0]))
            exit(1)

    elif argv[1] == '-c':
        try:
            run_client(*argv[2:])
        except Exception as e:
            print(e)
            print('usage: python {} -c <ip> <port> <input> <output>'.format(argv[0]))
            exit(1)