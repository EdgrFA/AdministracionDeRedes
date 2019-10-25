import telnetconnection
import json


def getTelnetDevices(topology, password, enable_password):
    devices = {}
    devices['dispositivo'] = []
    #Consultar todos los dispositivos
    for subred in topology['subred']:
        for host in subred['host']:
            devices.append(host)
    ##Conectar con telnet
    for device in devices:
        tn, mssg = telnetconnection.conectar_telnet(device, password, enable_password)
        if tn == None:
            print(mssg)
        else:
            print(mssg)
    return


filenameTopology = 'AdministradorDeRed/utils/topology.json'

with open(filenameTopology, 'r') as json_data:
    data = json.load(json_data)
    getTelnetDevices(data, '1234', '1234')

"""
data['subred'].append({
    'id': self.strIdSubred,
    'mascara' : self.strMascara,
    'broadcast': self.strBroadcast,
    'host' : hostData
})
"""