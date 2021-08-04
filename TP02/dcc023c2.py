from sys import argv
from utils.client import Client
from utils.server import Server

if __name__ == '__main__':
    node = Server(*argv[2:]) if argv[1] == '-s' else Client(*argv[2:])

    try:
        node.run()
    except KeyboardInterrupt as interrupt:
        print(interrupt)
        print('Encerrando antes do término da comunicação')