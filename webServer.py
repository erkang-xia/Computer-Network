# import socket module
from socket import *
import datetime
# In order to terminate the program
import sys


def webServer(port=13331):
    # The createServer() function begins by creating a new socket using the socket() function. The AF_INET parameter specifies that the socket should use IPv4 addressing,
    # and the SOCK_STREAM parameter specifies that the socket should use a stream-oriented protocol (TCP)
    serverSocket = socket(AF_INET, SOCK_STREAM)
    try:
        # Prepare a server socket
        serverSocket.bind(("127.0.0.1", port))
        serverSocket.listen(5);

        while True:
            # Establish the connection

            #print('Ready to serve...')
            connectionSocket, addr = serverSocket.accept()
            # When a client connects to the server, the accept() method is called on the serversocket object. This method blocks until a client connection is received,
            # at which point it returns a new socket object (clientsocket) that can be used to communicate with the client, as well as the client's address.

            message = connectionSocket.recv(5000).decode()
            # The code reads data from the client using the recv() method on clientsocket, which blocks until data is received. It then decodes the data into a string.

            #print(message)

            filename = message.split()[1]

            # opens the client requested file.
            # Plenty of guidance online on how to open and read a file in python. How should you read it though if you plan on sending it through a socket?
            f = open(filename[1:])
            outputdata = f.read()
            #print("outputdata:", outputdata)
            now = datetime.datetime.now()

            first_header = "HTTP/1.1 200 OK"
            # alive ={
            # 	"timeout":10,
            # 	"max":100,
            # }
            header_info = {
                "Date": now.strftime("%Y-%m-%d %H:%M"),
                "Content-Length": len(outputdata),
                "Keep-Alive": "timeout=%d,max=%d" % (10, 100),
                "Connection": "Keep-Alive",
                "Content-Type": "text/html"
            }
            following_header = "\r\n".join("%s:%s" % (item, header_info[item]) for item in header_info)
            #print("following_header:", following_header)
            connectionSocket.send(("%s\r\n%s\r\n\r\n" % (first_header, following_header)).encode())

            for i in range(0, len(outputdata)):
                connectionSocket.send(outputdata[i])
            connectionSocket.close()
    except Exception as e:
        # Send response message for file not found
        # Fill in start
        connectionSocket.send(
            "HTTP/1.1 404 Not Found\r\nContent-Type: text/html\r\n\r\n<!doctype html><html><body><h1>404 Not Found<h1></body></html>".encode())
        # Fill in end
        # Close client socket
        # Fill in start
        connectionSocket.close()
        # Fill in end
    #print("serverSocket closed")
    serverSocket.close()

    # Commenting out the below, as its technically not required and some students have moved it erroneously in the While loop. DO NOT DO THAT OR YOURE GONNA HAVE A BAD TIME.
    # serverSocket.close()
    # sys.exit()  # Terminate the program after sending the corresponding data


if __name__ == "__main__":
    webServer(13331)
