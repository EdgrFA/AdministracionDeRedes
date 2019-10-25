from multiprocessing.pool import ThreadPool
import telnetconnection
import threading
import shutil 
import json
import os

tftpServerPath = '/srv/tftp/'
tftpHost = '192.168.0.2'

def getDeviceInfo(ip, password, enable_password):
    tn, mssg = telnetconnection.conectar_telnet(ip, password, enable_password)
    if tn == None:
        return None
    hostname = telnetconnection.obtener_nombre_host(tn)
    localnets = telnetconnection.obtener_subredes_telnet(tn, False, 'L')
    print(hostname + ", " + str(localnets))
    ln = []
    for localnet in localnets:
        ln.append(localnet)

    device = []
    device.append({
        'name': hostname,
        'localip' : ln,
        'password' : password,
        'enable' : enable_password,
        'configfile': 'configFile' + hostname
    })
    return device


def getTelnetDevices(topology, password, enable_password):
    devices = {}
    devices['dispositivo'] = []
    #Consultar todos los routers
    for subred in topology['subred']:
        pool = ThreadPool(processes=5)
        async_results = []
        for host in subred['host']:
            #Comprobar si la ip corresponde con un router ya consultado
            exist = False
            for device in devices['dispositivo']:
                for ip in device['localip']:
                    if ip == host:
                        exist = True
                        break
            if exist:
                continue
            #Ejecutar hilos para obtener la informacion de los routers
            async_results.append(pool.apply_async(getDeviceInfo, (host, password, enable_password)))
        pool.close()
        pool.join()
        for async_result in async_results:
            result = async_result.get()
            if result != None:
                devices['dispositivo'].extend(result)
    return devices


def getConfigFile(device, filename =None):
    if filename == None:
        filename = device['name']
    if not os.path.isdir(tftpServerPath + device['name']):
        os.mkdir(tftpServerPath + device['name'])

    for ip in device['localip']:
        tn, mssg = telnetconnection.conectar_telnet(ip, device['password'], device['enable'])
        if tn == None:
            continue
        success = telnetconnection.obtener_archivo_configuracion(tn, tftpHost, filename)

        if success:
            while(True):
                try:
                    shutil.move(os.path.join(tftpServerPath, filename), os.path.join(tftpServerPath + device['name'], filename))
                    break
                except Exception as e:
                    print(e)
                    continue
            return True
    return False


#Faltaria revisar los cambios mientras el servidor no estaba arriba
def getConfigFiles(devices):
    threads = list()
    for device in devices['dispositivo']:
        pathFile =  device['name'] + "/" + device['configfile']
        if os.path.exists(tftpServerPath + pathFile):
            t = threading.Thread(target = getConfigFile, args = (device, 'SYSCONFIG' + device['configfile']))
        else:
            t = threading.Thread(target = getConfigFile, args = (device, ))
        threads.append(t)
        t.start()
    for t in threads:
        t.join()
    return


"""
filenameTopology = 'AdministradorDeRed/utils/topology.json'

with open(filenameTopology, 'r') as json_data:
    data = json.load(json_data)
    getTelnetDevices(data, '1234', '1234')
"""