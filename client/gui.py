import threading
import time
import tkinter as tk
import socket
import pickle
import random
import requests

import CLIENTCONFIG as CONFIG

#Defines Register screen
class Register(tk.Frame):
    def __init__(self, master):
        #Creates frame
        tk.Frame.__init__(self, master)
        
        #Defines tkinter objects
        self.label = tk.Label(self, text="Please enter your username to begin chatting")
        self.label.pack()

        self.username_entry = tk.Entry(self)
        self.username_entry.pack()

        self.register_button = tk.Button(self, text="Enter", command=self.register)
        self.register_button.pack()
    
    #Register function gets called upon button click
    def register(self):

        #Retrieves the username data in the entry box
        username = self.username_entry.get()
        try:
            #If username exists, client calls server endpoint for create user
            if username:
                response = requests.get(f'http://{CONFIG.IP}:{CONFIG.PORT}/user/create/{username}')
                response = response.json()
                print(response)
                self.master.user = {
                    'id': response['user']['id'],
                    'username': response['user']['name']
                }
                self.master.show_room_select()

        #Handles exception by displaying error to user
        except():
            self.label = self.label.config(text='There was an error creating user')
            print(f'Error creating user')

#Defines room screen
class Room(tk.Frame):
    def __init__(self, master, room_info, username):
        tk.Frame.__init__(self, master)
        #Contains messages on client side rather than db to maintain anonymity
        self.messages = []

        #Defines room information and required user information
        self.room_info = room_info
        self.username = username

        #Defines tkinter objects
        self.label = tk.Label(self, text=f"Connecting to room: {self.room_info['name']}")
        self.label.pack()

        self.message_entry = tk.Entry(self)
        self.message_entry.pack()

        self.send_button = tk.Button(self, text="Send", command=self.send_message)
        self.send_button.pack()

        self.messages_text = tk.Text(self, height=10, width=50)
        self.messages_text.pack()

        # Connect to the selected room
        self.connect_to_room()

    #Creates socket to connect to room given room_info
    def connect_to_room(self):
        # Establish socket connection to the room
        try:
            self.room_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.room_socket.connect((self.room_info["host"], self.room_info["port"]))
            print(f"Connected to room: {self.room_info['name']}")
            
            # Start receiving messages in a separate thread
            receive_thread = threading.Thread(target=self.receive_messages)
            receive_thread.daemon = True
            receive_thread.start()
            
        except Exception as e:
            self.label = tk.Label(self, text = f"Could not connect to {self.room_info['name']}")
            print(f"Error connecting to room: {e}")

    #Function executed upon message being sent from user
    def send_message(self):
        #Gets message in entry
        message = self.message_entry.get()
        #If message is not None, message is sent as a dictionary containing username and message
        if message:
            try:
                full_message = {'username': self.username, 'message': message}

                #Client socket sends to connected server socket for corresponding room
                self.room_socket.send(pickle.dumps(full_message))
                print(f"Sent message to room {self.room_info['name']}: {message}")
                self.message_entry.delete(0, tk.END)  # Clear the message entry
            except Exception as e:
                print(f"Error sending message to room {self.room_info['name']}: {e}")

    #In seperate thread, this function loops to recive messages
    def receive_messages(self):
        while True:
            #Upon receiving a message, it is decoded and appended to message array. display_messages() is then called to display the new messages
            try:
                full_message = pickle.loads(self.room_socket.recv(1024))
                if full_message:
                    print(f"Received message from room {self.room_info['name']}: {full_message['message']}")
                    self.messages.append(full_message)
                    self.display_messages()  # Update the displayed messages
            except Exception as e:
                print(f"Error receiving message from room {self.room_info['name']}: {e}")

    #Displays messages on screen
    def display_messages(self):
        self.messages_text.config(state=tk.NORMAL)  # Enable text widget for editing
        for msg in self.messages[-1:]:
            self.messages_text.insert(tk.END, msg['username'] + ": " + msg['message'] + '\n')
        self.messages_text.config(state=tk.DISABLED)

#Defines frame for room select screen
class RoomSelect(tk.Frame):
    def __init__(self, master):
        tk.Frame.__init__(self, master)

        self.label = tk.Label(self, text="Room Select")
        self.label.pack()
        
        self.room_labels = []

        # Button to create a new room
        self.create_room_button = tk.Button(self, text="Create New Room", command=self.create_room)
        self.create_room_button.pack()

    def update_room_list(self, server_instances):
        # Clear previous room labels
        for label in self.room_labels:
            label.destroy()
        self.room_labels.clear()

        # Create room labels from server instances
        for server_instance in server_instances:
            room_label = tk.Button(self, text=server_instance["name"], command=lambda info=server_instance: self.connect_to_room(info))
            room_label.pack()
            self.room_labels.append(room_label)

    def connect_to_room(self, room_info):
        response = requests.get(f'http://{CONFIG.IP}:{CONFIG.PORT}/user/addtoroom/{self.master.user["id"]}/{room_info["id"]}')
        response = response.json()
        print(response)
        code = response['code']

        if code == 200:
            print('Joined room successfully')
            # Hide the RoomSelect frame
            self.pack_forget()
            room_info['host'] = CONFIG.IP

            print(f'USER DATA AT THIS POINT {self.master.user}')
            # Show the Room frame
            room_frame = Room(self.master, room_info, self.master.user['username'])
            room_frame.pack()
        else:
            print(f'There was an error: Code {code}')
    
    def create_room(self):
        # Open the create room window
        create_room_window = CreateRoom(self.master)
        # Run the mainloop to display the window
        create_room_window.mainloop()

class CreateRoom(tk.Toplevel):
    def __init__(self, master):
        tk.Toplevel.__init__(self, master)
        self.title("Create New Room")

        self.label = tk.Label(self, text="Enter Room Name:")
        self.label.pack()

        self.room_name_entry = tk.Entry(self)
        self.room_name_entry.pack()

        self.create_button = tk.Button(self, text="Create", command=self.create_room)
        self.create_button.pack()

    def create_room(self):
        room_name = self.room_name_entry.get()
        if room_name:
            # Call the method to handle room creation
            try:
                response = requests.get(f'http://{CONFIG.IP}:{CONFIG.PORT}/room/create/{room_name}')
                response = response.json()
                if response['code'] == 200:
                    print('Successfully created room')
            except Exception as e:
                print(f'Could not create room: {e}')
            # Close the window after room creation
            self.destroy()

    def create_new_room(self):
        # Open the create room window
        create_room_window = CreateRoom(self.master)
        create_room_window.mainloop()
        
class Hush(tk.Tk):
    def __init__(self):
        tk.Tk.__init__(self)
        
        self.user = None
        self.server_instances = []
        
        self.title("Hush")
        self.geometry("400x300")
        
        self.registerscreen = Register(self)
        self.roomselectscreen = RoomSelect(self)
        
        self.show_register()
        self.search_thread = threading.Thread(target=self.searchForRooms)
        self.search_thread.daemon = True
        self.search_thread.start()

    def searchForRooms(self):
        while True:
            try:
                response = requests.get(f'http://{CONFIG.IP}:{CONFIG.PORT}/room/getrooms')
                if response.status_code == 200:
                    self.server_instances = response.json()['rooms']
                else:
                    print("Error: Unable to fetch rooms")
            except requests.exceptions.RequestException as e:
                print(f'Error fetching rooms: {e}')
            
            self.roomselectscreen.update_room_list(self.server_instances)
            
            # Wait for 3 seconds before querying again
            time.sleep(3)

    def show_register(self):
        """Show the register screen and hide room select screen"""
        self.roomselectscreen.pack_forget()
        self.registerscreen.pack()
    
    def show_room_select(self):
        """Show room select screen and hide register screen"""
        self.registerscreen.pack_forget()
        self.roomselectscreen.pack()


app = Hush()
app.mainloop()
