from utils.common import create_frames

class BaseNode:
    """
        Essa classe será usada para definir comportamentos similares tanto para
        a ponta ativa quanto para a ponta passiva
    """

    def __init__(self, input_file, output_file):
        # Criando quadros de envio
        with open(input_file, 'rb') as infile:
            self.send_frames = create_frames(infile.read())

        # Definindo lista de quadros de saída
        self.recv_frames = []
        self.output_file = output_file

