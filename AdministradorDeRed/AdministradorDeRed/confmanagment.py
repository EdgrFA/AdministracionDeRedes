from multiprocessing.pool import ThreadPool
import telnetconnection
import subprocess 
import threading
import shutil 
import json
import os

filenameDevicesConfig = 'AdministradorDeRed/utils/devicesConfigfile.json'
tftpServerPath = '/srv/tftp/'
tftpHost = '192.168.0.2'


def obtenerListaDispositivos():
    #Obtener lista de dispositivos
    try:
        with open(filenameDevicesConfig, 'r') as json_data:
            devices = json.load(json_data)
            return devices
    except Exception as e:
        print('no fue posible leer la lista de dispositivos' + str(e))
    return None


def getDeviceInfo(ip, password, enable_password):
    tn, mssg = telnetconnection.conectar_telnet(ip, password, enable_password)
    if tn == None:
        return None
    hostname = telnetconnection.obtener_nombre_host(tn)
    localnets = telnetconnection.obtener_subredes_telnet(tn, False, 'L')
    tn.close()
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
        filename = device['configfile']
    if not os.path.isdir(tftpServerPath + device['name']):
        os.mkdir(tftpServerPath + device['name'])

    for ip in device['localip']:
        tn, mssg = telnetconnection.conectar_telnet(ip, device['password'], device['enable'])
        if tn == None:
            continue
        success = telnetconnection.obtener_archivo_configuracion(tn, tftpHost, filename)
        tn.close()

        if success:
            while(True):
                try:
                    shutil.move(os.path.join(tftpServerPath, filename), 
                        os.path.join(tftpServerPath + device['name'], filename))
                    break
                except Exception as e:
                    print(e)
                    continue
            return True
    print('Telnet(' + device['name'] + '): No se pudo obtener archivo de configuracion.')
    return False


def getConfigFiles(devices):
    threads = list()
    for device in devices['dispositivo']:
        pathFile =  device['name'] + "/" + device['configfile']
        if not os.path.exists(tftpServerPath + pathFile):
            print('Obteniendo archivo de configuracion de router: ' + device['name'])
            t = threading.Thread(target = getConfigFile, args = (device, ))
            threads.append(t)
            t.start()
    for t in threads:
        t.join()
    return


def compareConfigFiles(pathFile, configFileName):
    print('Revisando: ' + configFileName)
    data = subprocess.Popen(['diff', 
            pathFile + configFileName, 
            pathFile + 'SYSCONFIG' + configFileName], 
            stdout = subprocess.PIPE)
    output = str(data.communicate()[0].decode('utf8'))
    data = output.split('\n')
    fecha = None
    equals = True
    for line in data:
        if line.find('Last configuration change at') != -1:
            fecha = line
        elif (line.find('>') != -1) or (line.find('<') != -1):
            #Se puede obtener la lista de cambios
            equals = False
            break
    
    if equals:
        shutil.move(os.path.join(pathFile, 'SYSCONFIG' + configFileName), 
            os.path.join(pathFile, configFileName))
        print('se remplazo archivo porque eran iguales')
    return equals, fecha


def sysconfigAlert(address):
    devices = obtenerListaDispositivos()
    #Buscar el dispositivo con la alerta 
    for device in devices['dispositivo']:
        for ip in device['localip']:
            if ip == address:
                print('Alerta en router: ' + device['name'] + '(' + ip + ')')
                t = threading.Thread(target = getConfigFile, args = (device, 'SYSCONFIG' + device['configfile']))
                t.start()
    return


def revisarCambios():
    devices = obtenerListaDispositivos()
    routersConCambios = {}
    routersConCambios['dispositivo'] = []

    for device in devices['dispositivo']:
        pathFile =  tftpServerPath + device['name'] + "/" 
        if os.path.exists(pathFile + device['configfile']) and os.path.exists(pathFile + 'SYSCONFIG' + device['configfile']):
            equals, fecha = compareConfigFiles(pathFile, device['configfile'])
            if not equals:
                routersConCambios['dispositivo'].append({
                    'router' : device['name'],
                    'file' : device['configfile'],
                    'fecha' : fecha})
                #Crear json con fecha y router
    return routersConCambios


def descartarCambios(configFileName):
    devices = obtenerListaDispositivos()
    for device in devices['dispositivo']:
        if device['configfile'] == configFileName:
            pathFile =  tftpServerPath + device['name'] + "/" 
            os.remove(os.path.join(pathFile, 'SYSCONFIG' + configFileName))
            for ip in device['localip']:
                tn, mssg = telnetconnection.conectar_telnet(ip, device['password'], device['enable'])
                if tn == None:
                    continue
                filePath = device['name'] + "/" + configFileName
                success = telnetconnection.restablecer_router_tftp(tn, tftpHost, filePath)
                tn.close()
                return True, 'Se restablecio router: ' + device['name']
    return False, 'No se pudo encontrar el archivo'


def sobrescribirCambios(configFileName):
    devices = obtenerListaDispositivos()
    for device in devices['dispositivo']:
        if device['configfile'] == configFileName:
            pathFile =  tftpServerPath + device['name'] + "/" 
            shutil.move(os.path.join(pathFile, 'SYSCONFIG' + configFileName), 
                os.path.join(pathFile, configFileName))
            return True, 'Se remplazo archivo de configuracion: ' + configFileName
    return False, 'No se pudo encontrar el archivo'


"""
filenameTopology = 'AdministradorDeRed/utils/topology.json'

with open(filenameTopology, 'r') as json_data:
    data = json.load(json_data)
    getTelnetDevices(data, '1234', '1234')
"""