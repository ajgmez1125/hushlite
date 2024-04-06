import random
import threading
from datetime import datetime

import requests
from server import TCPServer
import sqlite3
from flask import Flask, jsonify
from flask_cors import CORS, cross_origin

import CONFIG

#This is the server script that runs on the EC2 instance

#Starts a flask application
app = Flask(__name__)
cors = CORS(app)
app.config['CORS_HEADERS'] = 'Content-Type'

#Start script
def start():
    #Creates sqlite connection
    con = sqlite3.connect('hushdb')
    cur = con.cursor()

    #Drops tables if tables exist so that they can be recreated and repopulated upon startup. This will only run upon the server restarting
    try:
        cur.execute("DROP TABLE room")
        cur.execute("DROP TABLE user")
        cur.execute("DROP TABLE user_room")
    except:
        pass

    #Creates necessary tables for room, user, and intersection table for user_room. These tables are primarily used for auditing and don't serve much other purpose
    cur.execute("CREATE TABLE room(room_id, room_name, room_port, created)")
    cur.execute("CREATE TABLE user(user_id, username, created)")
    cur.execute("CREATE TABLE user_room(user_id, room_id, joined)")

    #Default room configs
    room_configs = [
        {"port": 62672, "name": "Celestes Room"},
        {"port": 43247, "name": "Ralsei's Room"},
        {"port": 44678, "name": "Boys Rool Girls Drool"}
    ]

    #Iterates through room configs and creates new rooms in database room table
    for i in range(0, len(room_configs)):
        room_size = cur.execute("SELECT COUNT(*) FROM room")
        room_size = room_size.fetchone()
        cur.execute(f"INSERT INTO room VALUES (?,?,?,?)", (
            room_size[0] + 1,
            room_configs[i]['name'],
            room_configs[i]['port'],
            datetime.now()
            ))
        con.commit()

    #Selects newly added rows from room table and starts socket instances
    rooms = cur.execute('SELECT * FROM room')
    rooms = rooms.fetchall()
    print(rooms)
    for room in rooms:
        startRoom(room[2], room[1])

#Private function for starting a new room instance using a new thread
def startRoom(port, name):
    server_instance = TCPServer(CONFIG.IP, port, name)
    process = threading.Thread(target=server_instance.start)
    process.daemon = True
    process.start()

#Endpoint for creating new user
@app.route('/user/create/<username>')
def createUser(username):
    #Attempts to create new user, if this fails the response returned will signify a failure, else, it returns a success message followed by the result of querying the new user
    try:
        #Creates sqlite connection and cursor
        con = sqlite3.connect('hushdb')
        cur = con.cursor()

        #Querys user table size to assign new room id
        user_size = cur.execute('SELECT COUNT(*) FROM user')
        user_size = user_size.fetchone()[0]
        cur.execute("INSERT INTO user VALUES (?,?,?)", (
            user_size + 1,
            username,
            datetime.now()
            ))
        con.commit()

        #Querys newly created room and returns its data
        user = cur.execute('SELECT * FROM user WHERE user_id = ?', (user_size + 1,))
        user = user.fetchone()
        print(f'/user/create fetched user {user}')
        return(jsonify({
            'code': 200,
            'user': {
                'id': user[0],
                'name': user[1]
            }
        }))
    except Exception as e:
        print('/user/create/<username> RAN INTO AN ERROR')
        return(jsonify({
            'code': 500,
            'message': str(e)
        }))

#Endpoint for creating room
@app.route('/room/create/<roomName>')
def createRoom(roomName):
    #Attempts to create new room, if this fails the response returned will signify a failure, else, it returns a success message followed by the result of querying the new room data
    try:
        #Creates sqlite connection and cursor
        con = sqlite3.connect('hushdb')
        cur = con.cursor()

        #Querys room table size to assign new room id
        room_size = cur.execute('SELECT COUNT(*) FROM room')
        room_size = room_size.fetchone()[0]

        #Port is randomly chosen (since there are so many ports to choose from the chances of an in use port being choosen is less than 1%)
        port = random.randint(49152, 65535)
        cur.execute("INSERT INTO room VALUES (?,?,?,?)", (
            room_size + 1,
            roomName,
            port,
            datetime.now()
            ))

        #Starts room and commits changes to db
        startRoom(port, roomName)
        con.commit()

        #Querys newly created room and returns its data
        room = cur.execute('SELECT * FROM room WHERE room_id = ?', (room_size + 1,))
        room = room.fetchone()
        print(f'/room/create fetched room {room}')
        return(jsonify({
            'code': 200,
            'room': {
                'id': room[0],
                'name': room[1],
                'port': room[2]
            }
        }))
    except Exception as e:
        return(jsonify({
            'code': 500,
            'message': str(e)
        }))

#Endpoint to get all rooms in room table
@app.route('/room/getrooms')
def getAllRooms():
    #Attempts to query all rooms, if this fails the response returned will signify a failure, else, it returns a success message followed by the array of rooms
    try:
        #Creates sqlite connection and cursor
        con = sqlite3.connect('hushdb')
        cur = con.cursor()

        #Selects all rooms
        rooms = cur.execute('SELECT * FROM room')
        rooms = rooms.fetchall()
        print('FETCHED ROOMS: ' + str(rooms))

        #Adds all rooms from array of tuples to array of dictionaries
        roomsArr = []
        for room in rooms:
            roomsArr.append({
                'id': room[0],
                'name': room[1],
                'port': room[2]
            })

        #Returns array of room dictionary data
        return(jsonify({
            'code': 200,
            'rooms': roomsArr
        }))
    except Exception as e:
        return(jsonify({
            'code': 500,
            'message': str(e)
        }))

#Endpoint to add user to a room by inserting into user_room table
@app.route('/user/addtoroom/<user_id>/<room_id>')
def addToRoom(user_id, room_id):
    try:
        con = sqlite3.connect('hushdb')
        cur = con.cursor()
        cur.execute("INSERT INTO user_room VALUES (?,?,?)", (
            user_id,
            room_id,
            datetime.now()
            ))
        con.commit()
        return(jsonify({
            'code': 200,
            'message': 'Success'
        }))
    except Exception as e:
        return(jsonify({
            'code': 500,
            'message': str(e)
        }))

if __name__ == "__main__":
    start()
    app.run(host=CONFIG.IP, port=CONFIG.PORT)
