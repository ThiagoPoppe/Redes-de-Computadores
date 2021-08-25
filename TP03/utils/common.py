from struct import pack, unpack

from .constants import BUFSZ
from .constants import SERVER_ID

type_encoder = {
    'OK': 1, 'ERRO': 2, 'OI': 3,
    'FLW': 4, 'MSG': 5, 'CREQ': 6,
    'CLIST': 7, 'FILE': 8, 'FILE_CHUNK': 9
}

type_decoder = {value:key for key, value in type_encoder.items()}

def is_sender(id):
    return id >= 1 and id <= (2**12 - 1)

def is_displayer(id):
    return id >= 2**12 and id <= (2**13 - 1)

def recv_expected_length(sock, expected_length):
    """
        Método auxiliar para lermos uma quantidade esperada de bytes de um recv.
        O método pode gerar uma excessão ``RuntimeError`` indicando um erro na comunicação.
    """

    buffer = b''
    bytes_received = 0

    while bytes_received < expected_length:            
        data = sock.recv(min(expected_length - bytes_received, BUFSZ))
        if not data:
            raise RuntimeError('connection terminated unexpectedly')

        buffer += data
        bytes_received = bytes_received + len(data)

    return buffer

def recv_ok_message(sock, expected_header):
    """ 
        Função auxiliar para verificarmos se os próximos bytes representam um OK.
        Essa função retornará True caso recebermos um OK válido e False caso contrário
    """

    header = recv_expected_length(sock, 8)
    header = unpack('!4H', header)
    return header == expected_header

def initialize_client(sock, ip, host, source_id):
    """ Função para inicializar um cliente, retornando o seu ID """

    sock.connect((ip, int(host)))

    # Enviando mensagem de OI para conectar ao servidor
    send_oi_message(sock, source_id, 0)

    # Verificando se recebemos um OK do servidor
    header = recv_expected_length(sock, 8)
    header = unpack('!4H', header)

    if type_decoder[header[0]] == 'OK':
        client_id = header[2]
        print('< Welcome, client! Your id is: {}\n'.format(client_id))
    else:
        print('< something went wrong, please try again')
        exit(1)

    return client_id


###### FUNÇÕES PARA CRIAR E ENVIAR MENSAGENS ######

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