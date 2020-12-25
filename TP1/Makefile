CC = g++
CFLAGS = -Wall -std=c++11

servidor:
	$(CC) $(CFLAGS) -c ClientTags.cpp
	$(CC) $(CFLAGS) ClientTags.o servidor.cpp -o servidor -lpthread

cliente:
	$(CC) $(CFLAGS) cliente.cpp -o cliente

clean:
	rm *.o cliente servidor

.PHONY: servidor cliente