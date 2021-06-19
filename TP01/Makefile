all:
	gcc -Wall -c common.c
	gcc -Wall -c location_array.c
	gcc -Wall client.c common.o -o cliente
	gcc -Wall server.c common.o location_array.o -o servidor