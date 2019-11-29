import os
import json

def ls(ruta = os.getcwd()):
    return [arch.name for arch in os.scandir(ruta)]


def obtenerNerflowInfo(netflowPath):
    routers = ls(netflowPath)
    data = {}
    data['router'] = []

    for router in routers:
        clientes = ls(netflowPath + '/' + router)
        usersData = []
        clstr = None
        for cl in clientes:
            clstr = cl
            usuarios = ls(netflowPath + '/' + router + '/' + cl)
            for usuario in usuarios:
                fechas = []
                with open(netflowPath + '/' + router + '/' + cl + '/' +  usuario, 'r') as json_data:
                    userJson = json.load(json_data)
                    for registro in userJson['registro']:
                        fechas.append(registro['year'] + '-' + registro['month'])
                usersData.append({
                    'usuario' : usuario,
                    'fechas' : fechas
                })
        #Agregar informacion al json
        data['router'].append({
            'nombre' : str(router),
            'cliente' : str(clstr),
            'usuarios' : usersData
        })
    return json.dumps(data)