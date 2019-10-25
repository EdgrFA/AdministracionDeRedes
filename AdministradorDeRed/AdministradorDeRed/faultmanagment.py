from os import remove
import socket
import json
import datetime


filenameTraps = 'AdministradorDeRed/utils/traps.json'
filenameSyslog = 'AdministradorDeRed/utils/logging.json'

def fooTraps(newmssg):
    currentDT = datetime.datetime.now()
    try:
        with open(filenameTraps, 'r') as json_data:
            data = json.load(json_data)
            data['traps'].append({
                'mssg': newmssg,
                'time': str(currentDT)})
            with open(filenameTraps, 'w+') as json_data: 
                json.dump(data, json_data)
    except:
        data = {}
        data['traps'] = []
        data['traps'].append({
                'mssg': newmssg,
                'time': str(currentDT)})
        with open(filenameTraps, 'w') as json_data: 
            json.dump(data, json_data)


def trap_receiver():
    #Delete traps file
    try:
        remove(filenameTraps)
    except:
        pass

    # Create a UDP socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    # Bind the socket to the port
    server_address = ('', 8081)
    print('starting trap service up on {} port {}'.format(*server_address))
    sock.bind(server_address)
    while True:
        mssg, address = sock.recvfrom(4096)
        print('Trap-service:received {} bytes from {}'.format(len(mssg), address))
        print(mssg.decode('utf-8'))
        fooTraps(mssg.decode('utf-8'))


def fooSyslog(newmssg, address):
    currentDT = datetime.datetime.now()
    try:
        with open(filenameSyslog, 'r') as json_data:
            data = json.load(json_data)
            data['notification'].append({
                'mssg': newmssg,
                'address': address})
            with open(filenameSyslog, 'w+') as json_data: 
                json.dump(data, json_data)
    except:
        data = {}
        data['notification'] = []
        data['notification'].append({
                'mssg': newmssg,
                'address': address})
        with open(filenameSyslog, 'w') as json_data: 
            json.dump(data, json_data)


def syslog_receiver():
    #Delete logging file
    try:
        remove(filenameSyslog)
    except:
        pass

    # Create a UDP socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    # Bind the socket to the port
    server_address = ('', 8082)
    print('starting trap service up on {} port {}'.format(*server_address))
    sock.bind(server_address)
    while True:
        mssg, address = sock.recvfrom(4096)
        print('Trap-service:received {} bytes from {}'.format(len(mssg), address))
        print(mssg.decode('utf-8'))
        fooSyslog(mssg.decode('utf-8'), address)


def getJsonTraps():
    try:
        with open(filenameTraps, 'r') as json_data:
            data = json.load(json_data)
            remove(filenameTraps)
            return data
    except:
        return None

def getJsonSyslog():
    try:
        with open(filenameSyslog, 'r') as json_data:
            data = json.load(json_data)
            remove(filenameSyslog)
            return data
    except:
        return None