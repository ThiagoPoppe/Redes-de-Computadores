from utils.common import is_displayer
from utils.constants import SERVER_ID

def validate_oi_message(source_id, dest_id, displayers):
    """ 
        Função auxiliar para validarmos uma mensagem de OI.
        Essa função 0 quando devemos criar um exibidor e 1 se for um emissor.
        Essa função também retornará -1 se houver algum "erro" durante a valicação.
    """

    # Verificando se estamos associando um exibidor que não existe
    if is_displayer(source_id) and source_id not in displayers:
        print('< trying to establish association with non-existent displayer')
        return -1

    # Verificando se a mensagem de OI não foi direcionada para o servidor
    if dest_id != SERVER_ID:
        print('< OI message not directed to server')
        return -1

    return 0 if (source_id == 0) else 1