from confmanagment import getConfigFiles, getTelnetDevices, revisarCambios, descartarCambios, sobrescribirCambios
from telnetconnection import conectar_telnet, obtener_subredes_telnet
from flask import Flask, render_template, request, flash, abort
import faultmanagment
import pingpuller
import threading
import json
import sys
import os


app = Flask(__name__)
app.secret_key = "12345"
filenameTopology = 'AdministradorDeRed/utils/topology.json'
filenameDevicesConfig = 'AdministradorDeRed/utils/devicesConfigfile.json'


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/ping-puller', methods=['GET', 'POST'])
def getPingPuller():
    if request.method == 'GET':
        return render_template('ping-puller.html')

    if request.method == 'POST':
        telnet_host = request.form['host']
        passsword = request.form['telnet_password']
        enable_password = request.form['enable_password']
        tn, mssg = conectar_telnet(telnet_host, passsword, enable_password)
        if tn == None:
            if mssg.find("Interrupcion") != -1:
                abort(502)
            else:
                abort(401)

        subnets = obtener_subredes_telnet(tn)
        tn.close()

        data = pingpuller.getJsonPingPuller(subnets)
        file = open(filenameTopology, 'w') 
        file.write(data)
        return data
    return render_template('index.html')


@app.route('/fault-managment', methods=['GET', 'POST'])
def getFaultManagment():
    if request.method == 'GET':
        threading.Thread(target=faultmanagment.trap_receiver).start()
        threading.Thread(target=faultmanagment.syslog_receiver).start()
        return render_template('fault-managment.html')

    if request.method == 'POST':
        data = None
        elementoRequerido = request.form['element']
        if elementoRequerido == 'traps':
            data = faultmanagment.getJsonTraps()
            if data == None:
                abort(404)
        else:
            data = faultmanagment.getJsonSyslog()
            if data == None:
                abort(404)
        return data
    return render_template('index.html')


@app.route('/config-managment', methods=['GET', 'POST'])
def getConfigManagment():
    if request.method == 'GET':        
        if  os.path.exists(filenameTopology):
            if os.path.exists(filenameDevicesConfig):
                return render_template('config-managment.html')
            else:
                return render_template('connect-devices.html')
        else:
            return render_template('ping-puller.html')
    if request.method == 'POST':
        data = None
        with open(filenameDevicesConfig, 'r') as json_data:
            data = json.load(json_data)
        getConfigFiles(data)
        threading.Thread(target=faultmanagment.syslog_receiver).start() #Cambiar hilo de modo que solo escuche los SYSLOGCONFIG
        return data
    return render_template('index.html')


@app.route('/connect-devices', methods=['GET', 'POST'])
def connectDevices():
    if request.method == 'GET':
        if  os.path.exists(filenameTopology):
            return render_template('connect-devices.html')
        else:
            return render_template('ping-puller.html')

    if request.method == 'POST':
        passsword = request.form['telnet_password']
        enable_password = request.form['enable_password']
        try:
            data = None
            with open(filenameTopology, 'r') as json_data:
                data = json.load(json_data)
            devices = getTelnetDevices(data, passsword, enable_password)
            file = open(filenameDevicesConfig, 'w') 
            file.write(json.dumps(devices))
            return render_template('config-managment.html')
        except:
            abort(502)
        #Revisar si sigue existiendo topology.json
    return render_template('index.html')

    
@app.route('/file-monitor', methods=['GET', 'PUT', 'DELETE'])
def fileMonitor():
    if request.method == 'GET':
        data = revisarCambios()
        data = json.dumps(data)
        return data
        #Enviar mensaje al servidor si se desean reemplazar los cambios
        #Talvez enviar la hora de creacion del nuevo archivo de configuracion
    if request.method == 'PUT':
        configFileName = request.form['file']
        success, mssg = sobrescribirCambios(configFileName)
        print('res: ' + mssg)
        if not success:
            abort(404)
        return 'OK'
    if request.method == 'DELETE':
        configFileName = request.form['file']
        success, mssg = descartarCambios(configFileName)
        print('res: ' + mssg)
        if not success:
            abort(404)
        return 'OK'
    return


if __name__ == '__main__':
    app.run(host="192.168.0.2", port=int("8080"), debug=True)