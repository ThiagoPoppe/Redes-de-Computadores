from struct import pack

from .common import type_encoder
from .constants import SERVER_ID

def send_ok_message(sock, source_id, dest_id, seq_number):
    message = [type_encoder['OK'], source_id, dest_id, seq_number]
    message = pack('!4H', *message)
    sock.sendall(message)

def send_erro_message(sock, source_id, dest_id, seq_number):
    message = [type_encoder['ERRO'], source_id, dest_id, seq_number]
    message = pack('!4H', *message)
    sock.sendall(message)

def send_oi_message(sock, source_id, seq_number):
    message = [type_encoder['OI'], source_id, SERVER_ID, seq_number]
    message = pack('!4H', *message)
    sock.sendall(message)

def send_flw_message(sock, source_id, dest_id, seq_number):
    message = [type_encoder['FLW'], source_id, dest_id, seq_number]
    message = pack('!4H', *message)
    sock.sendall(message)

def send_msg_message(sock, source_id, dest_id, seq_number, ascii_msg):
    n_bytes = len(ascii_msg)

    header = [type_encoder['MSG'], source_id, dest_id, seq_number]
    header = pack('!4H', *header)

    fmt = '!H{}s'.format(n_bytes)
    message = header + pack(fmt, n_bytes, ascii_msg)
    sock.sendall(message)

def send_creq_message(sock, source_id, dest_id, seq_number):
    message = [type_encoder['CREQ'], source_id, dest_id, seq_number]
    message = pack('!4H', *message)
    sock.sendall(message)

def send_clist_message(sock, source_id, dest_id, seq_number, client_list):
    n_clients = len(client_list)

    header = [type_encoder['CLIST'], source_id, dest_id, seq_number]
    header = pack('!4H', *header)

    fmt = '!H{}H'.format(n_clients)
    message = header + pack(fmt, n_clients, *client_list)
    sock.sendall(message)

def send_file_message(sock, source_id, dest_id, seq_number, file_id, n_chunks, file_ext):
    ascii_ext = file_ext.encode('ascii')
    len_ext = len(ascii_ext)

    header = [type_encoder['FILE'], source_id, dest_id, seq_number]
    header = pack('!4H', *header)

    fmt = '!3H{}s'.format(len_ext)
    message = header + pack(fmt, file_id, n_chunks, len_ext, ascii_ext)
    sock.sendall(message)

def send_file_chunk_message(sock, source_id, dest_id, seq_number, file_id, chunk_id, chunk):
    len_chunk = len(chunk)

    header = [type_encoder['FILE_CHUNK'], source_id, dest_id, seq_number]
    header = pack('!4H', *header)

    fmt = '!3H{}s'.format(len_chunk)
    message = header + pack(fmt, file_id, chunk_id, len_chunk, chunk)
    sock.sendall(message)