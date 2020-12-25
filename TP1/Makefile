CC = g++
CFLAGS = -Wall -std=c++11

servidor:
	$(CC) $(CFLAGS) -c ClientTags.cpp Utils.c
	$(CC) $(CFLAGS) ClientTags.o Utils.o servidor.c -o servidor

cliente:
	$(CC) $(CFLAGS) -c Utils.c
	$(CC) $(CFLAGS) Utils.o cliente.c -o cliente

clean:
	rm *.o cliente servidor

.PHONY: servidor cliente