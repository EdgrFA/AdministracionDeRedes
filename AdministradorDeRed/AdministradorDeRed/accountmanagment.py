"""
Example collector script for NetFlow v1, v5, and v9.
This file belongs to https://github.com/bitkeks/python-netflow-v9-softflowd.

Copyright 2017-2019 Dominik Pataky <dev@bitkeks.eu>
Licensed under MIT License. See LICENSE.
"""

import argparse
from collections import namedtuple
from datetime import date
import queue
import gzip
import json
import logging
import sys
import socketserver
import threading
import time
import os

from v5 import V5ExportPacket

PACKET_TIMEOUT = 60 * 60

RawPacket = namedtuple('RawPacket', ['ts', 'client', 'data'])
filenameDevicesConfig = 'AdministradorDeRed/utils/devicesConfigfile.json'

class QueuingRequestHandler(socketserver.BaseRequestHandler):
    def handle(self):
        data = self.request[0]  # get content, [1] would be the socket
        self.server.queue.put(RawPacket(time.time(), self.client_address, data))


class QueuingUDPListener(socketserver.ThreadingUDPServer):
    def __init__(self, interface, queue):
        self.queue = queue
        super().__init__(interface, QueuingRequestHandler)


class NetFlowListener(threading.Thread):

    def __init__(self, host, port):
        self.output = queue.Queue()
        self.input = queue.Queue()
        self.server = QueuingUDPListener((host, port), self.input)
        self.thread = threading.Thread(target=self.server.serve_forever)
        self.thread.start()
        self._shutdown = threading.Event()
        super().__init__()

    def get(self, block=True, timeout=None):
        return self.output.get(block, timeout)

    def run(self):
        try:
            templates = {}
            to_retry = []
            while not self._shutdown.is_set():
                try:
                    pkt: RawPacket = self.input.get(block=True, timeout=0.5)
                except queue.Empty:
                    continue
                export = V5ExportPacket(pkt.data)
                print("Processed a v " + str(export.header.version) + " ExportPacket with " + str(export.header.count) + " flows.")
                if export.header.version == 9 and export.contains_new_templates and to_retry:
                    for p in to_retry:
                        self.input.put(p)
                    to_retry.clear()

                self.output.put((pkt.ts, pkt.client, export))
        finally:
            self.server.shutdown()
            self.server.server_close()

    def stop(self):
        self._shutdown.set()

    def join(self, timeout=None):
        self.thread.join(timeout=timeout)
        super().join(timeout=timeout)


def get_export_packets(host, port):
    listener = NetFlowListener(host, port)
    listener.start()
    try:
        while True:
            yield listener.get()
    finally:
        listener.stop()
        listener.join()

def obtenerListaDispositivos():
    #Obtener lista de dispositivos
    try:
        with open(filenameDevicesConfig, 'r') as json_data:
            devices = json.load(json_data)
            return devices
    except Exception as e:
        print('no fue posible leer la lista de dispositivos' + str(e))
    return None

def buscarRouter(interfaz):
    devices = obtenerListaDispositivos()
    router = None
    for device in devices['dispositivo']:
        for ip in device['localip']:
            if ip == interfaz:
                router = device
                return router


def agregarUsuarioConsumo(usuario, paquetes, path):
    fecha = date.today()
    try:
        with open(path + usuario, 'r') as json_data:
            data = json.load(json_data)
            nuevoDia = True
            for registro in data['registro']:
                if str(fecha.day) == registro['day']: ##### Parse ???
                    registro['paquetes'] = str(int(registro['paquetes']) + paquetes)
                    nuevoDia = False
                    break

            if nuevoDia:
                data['registro'].append({
                    'año' : str(fecha.year),
                    'month' : str(fecha.month),
                    'day' : str(fecha.day),
                    'paquetes' : str(registro['paquetes'])
                })
            with open(path + usuario, 'w+') as json_data: 
                json.dump(data, json_data)
    except:
        data = {}
        data['registro'] = []
        data['registro'].append({
            'year' : str(fecha.year),
            'month' : str(fecha.month),
            'day' : str(fecha.day),
            'paquetes' : str(paquetes)
        })
        with open(path + usuario, 'w') as json_data: 
            json.dump(data, json_data)
            

def netFlowService(host, port, netflowPath):
    try:
        for ts, client, export in get_export_packets(host, port):
            path = netflowPath
            fecha = date.today()
            #Buscar de quien es la interfaz que se recibio
            router = buscarRouter(client[0])
            #Organizar datos por router y luego interfaz 
            if not os.path.isdir(path):
                os.mkdir(path)
            path = path + router['name']
            if not os.path.isdir(path):
                os.mkdir(path)
            path = path + '/' + client[0]
            if not os.path.isdir(path):
                os.mkdir(path)
            path = path + '/'
            
            usuarios = None
            try:
                with open(path, 'r') as json_data:
                    usuarios = json.load(json_data)
            except:
                usuarios = {}
                usuarios['usuario'] = []

            #Obtener numero de paquetes por usuario
            for flow in export.flows:
                f = flow.data
                if client[0] != f['IPV4_SRC_ADDR']:
                    agregarUsuarioConsumo(f['IPV4_SRC_ADDR'], int(f['IN_PACKETS']), path)
                if client[0] != f['IPV4_DST_ADDR']:
                    agregarUsuarioConsumo(f['IPV4_DST_ADDR'], int(f['IN_PACKETS']), path)

            print('Cliente: ' + router['name'] + ': ' + client[0])
    except KeyboardInterrupt:
        print("Received KeyboardInterrupt, passing through")
        pass

#Este programa se debe ejecutar como demonio para que funcione el sistema
netFlowService(host="192.168.0.2", port = 9000, netflowPath = 'AdministradorDeRed/netflow/')