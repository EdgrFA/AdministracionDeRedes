import os
import json

def ls(ruta = os.getcwd()):
    return [arch.name for arch in os.scandir(ruta)]


def obtenerNeflowClients(netflowPath):
    routers = ls(netflowPath)
    data = {}
    data['router'] = []

    for router in routers:
        clientes = ls(netflowPath + '/' + router)
        usersData = []
        clstr = None
        for cl in clientes:
            clstr = cl
        #Agregar informacion al json
        data['router'].append({
            'nombre' : str(router),
            'cliente' : str(clstr)
        })
    return json.dumps(data)

def obtenerUsuarios(netflowPath):
    users = ls(netflowPath)
    return json.dumps(users)

def obtenerFechas(netflowPath):
    fechas = []
    with open(netflowPath, 'r') as json_data:
        userJson = json.load(json_data)
        for registro in userJson['registro']:
            fechas.append(registro['fecha'])
    return json.dumps(fechas)

def obtenerRegistro(netflowPath, fecha):
    with open(netflowPath, 'r') as json_data:
        userJson = json.load(json_data)
        for registro in userJson['registro']:
            if str(fecha) == str(registro['fecha']):
                datos = [{'hour' : 'Hora 0', 'y': '0'}]
                acumulado = 0
                horaActual = 0
                for consumo in registro['consumo']:
                    acumulado += int(consumo['paquetes'])
                    while horaActual != int(consumo['hora']:
                        datos.append({
                            'hour' : 'Hora ' + str(horaActual + 1),
                            'kb' : str(acumulado/1000)
                        })
                        horaActual += 1 

                    datos.append({
                        'hour' : 'Hora ' + str(int(consumo['hora']) + 1),
                        'kb' : str(acumulado/1000)
                    })
                    horaActual += 1
                return json.dumps(datos)
    return None