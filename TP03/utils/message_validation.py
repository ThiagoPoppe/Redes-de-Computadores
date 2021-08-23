from utils.common import is_displayer
from utils.constants import SERVER_ID

def validate_oi_message(source_id, dest_id, displayers):
    """ Retorna -1 em caso de erro, 0 quando devemos inicializar um exibidor e 1 se for um emissor """

    # Verificando se estamos associando um exibidor que não existe
    if is_displayer(source_id) and source_id not in displayers:
        return -1

    # Verificando se a mensagem de OI não foi direcionada para o servidor
    if dest_id != SERVER_ID:
        return -1

    return 0 if (source_id == 0) else 1