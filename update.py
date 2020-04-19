import socket
import json

def send_to_server(js):
    """Open socket and send the json string js to server with EOM appended, and wait
    for \n terminated reply.
    js - json object to send to server
    """
    clientsocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    clientsocket.connect(('128.250.106.25', 5002))
    clientsocket.send("""{}EOM""".format(js).encode('utf-8'))
    data = ''

    while data == '' or data[-1] != "\n":
        data += clientsocket.recv(1024).decode('utf-8')
    print(data)
    clientsocket.close()
    
file1 = open('Player.py', 'r') 
lines = file1.readlines() 
output = "".join(lines)


request = {
    "cmd": "ADD",
    "syn": 12,
    "name": "dummy",
    "data": output
}

request = json.dumps(request)

send_to_server(request)