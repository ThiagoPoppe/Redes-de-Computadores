from struct import pack

from .common import type_encoder
from .constants import SERVER_ID

def create_message_header(message_type, source_id, dest_id, seq_number):
    """ Função auxiliar para criarmos o cabeçalho das mensagens """

    header = [type_encoder[message_type], source_id, dest_id, seq_number]
    header = pack('!4H', *header)
    return header

def send_header_only_message(sock, message_type, source_id, dest_id, seq_number):
    """ Função auxiliar para enviarmos mensagens que apenas possuem o cabeçalho """

    header = create_message_header(message_type, source_id, dest_id, seq_number)
    sock.sendall(header)

def send_ok_message(sock, source_id, dest_id, seq_number):
    send_header_only_message(sock, 'OK', source_id, dest_id, seq_number)

def send_erro_message(sock, source_id, dest_id, seq_number):
    send_header_only_message(sock, 'ERRO', source_id, dest_id, seq_number)

def send_oi_message(sock, source_id, seq_number):
    send_header_only_message(sock, 'OI', source_id, SERVER_ID, seq_number)

def send_flw_message(sock, source_id, dest_id, seq_number):
    send_header_only_message(sock, 'FLW', source_id, dest_id, seq_number)

def send_creq_message(sock, source_id, dest_id, seq_number):
    send_header_only_message(sock, 'CREQ', source_id, dest_id, seq_number)

def send_msg_message(sock, source_id, dest_id, seq_number, ascii_msg):
    n_bytes = len(ascii_msg)
    header = create_message_header('MSG', source_id, dest_id, seq_number)

    fmt = '!H{}s'.format(n_bytes)
    message = header + pack(fmt, n_bytes, ascii_msg)
    sock.sendall(message)

def send_clist_message(sock, source_id, dest_id, seq_number, client_list):
    n_clients = len(client_list)
    header = create_message_header('CLIST', source_id, dest_id, seq_number)

    fmt = '!H{}H'.format(n_clients)
    message = header + pack(fmt, n_clients, *client_list)
    sock.sendall(message)

def send_file_message(sock, source_id, dest_id, seq_number, file_id, n_chunks, ascii_ext):
    len_ext = len(ascii_ext)
    header = create_message_header('FILE', source_id, dest_id, seq_number)

    fmt = '!3H{}s'.format(len_ext)
    message = header + pack(fmt, file_id, n_chunks, len_ext, ascii_ext)
    sock.sendall(message)

def send_file_chunk_message(sock, source_id, dest_id, seq_number, file_id, chunk_id, chunk):
    len_chunk = len(chunk)
    header = create_message_header('FILE_CHUNK', source_id, dest_id, seq_number)

    fmt = '!3H{}s'.format(len_chunk)
    message = header + pack(fmt, file_id, chunk_id, len_chunk, chunk)
    sock.sendall(message)