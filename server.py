import pickle
import socket
import threading

#Class that defines logic for room sockets
class TCPServer:
    #Constructor takes params for host ip, port, and room name
    def __init__(self, host, port, name):
        self.name = name
        self.host = host
        self.port = port

        #Array that stores client data
        self.clients = []

        #Creates a new socket, binds to port and host, and listens
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.bind((self.host, self.port))

        print(f"Server listening on {self.host}:{self.port}")

    #Function to handle clients
    def handle_client(self, client_socket, client_address):
        print(f"Accepted connection from {client_address}")
        #Adds client to the client array
        self.clients.append(client_socket)
        #Starts a while loop that listens for client messages
        while True:
            #Attempts to retrieve the full message which consists of a dictionary with a username and a message
            try:
                full_message = pickle.loads(client_socket.recv(1024))
                #If the full message isnt None, the message is broadcasted to all the other clients in the array
                if full_message:
                    print(f"Received from {client_address}: {full_message['message']}")
                    self.broadcast(pickle.dumps(full_message))
                else:
                    print(f"All quiet here")
                    break
            #Catches connection exception in the case of a client leaving
            except ConnectionResetError:
                print(f"Client {client_address} disconnected unexpectedly")
                break

    def broadcast(self, message):
        for client_socket in self.clients:
            try:
                client_socket.send(message)
            except Exception as e:
                print(f"Error broadcasting message to a client: {e}")

    #While constructor binds the socket, this script serves as the actual starting point for the sockets functionality, without it, the socket doesnt really do much
    def start(self):
        #Starts listening
        self.server_socket.listen(5)

        #For loop waits for incoming clients
        while True:
            #Upon receiving a client the server will accept the connection
            client_socket, client_address = self.server_socket.accept()

            #A new client thread will start the handle_client function
            client_handler = threading.Thread(target=self.handle_client, args=(client_socket, client_address))
            client_handler.daemon = True
            client_handler.start()

#This is only called if the server.py script is run itself which it never is, this is just a remnant of code from testing
if __name__ == "__main__":
    HOST = '127.0.0.1'
    PORT = 12345
    server = TCPServer(HOST, PORT, "MyServer")
    server.start()
