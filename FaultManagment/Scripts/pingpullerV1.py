from ipaddress import IPv4Network
import xml.etree.ElementTree as ET
import subprocess  # For executing a shell command
import telnetlib
import threading
import re

#def filtrar_subredes():

def conectar_telnet(ip, passwordTelnet, passwordEnable = None):
	#try:
	print("Telnet: Conectandose con " + ip + " ...")
	tn = telnetlib.Telnet(ip.encode('utf-8'))
	#tn.set_debuglevel(9)
	tn.read_until(b'Password: ', 8)
	tn.write(passwordTelnet.encode('utf-8') + b'\n')
	tn.read_until(b'>', 8)
	print("Telnet: Conexión exitosa.")
	
	if passwordEnable != None :
		#Habilitar modo enable
		print("Telnet: Habilitando modo Enable.")
		tn.write(b'enable\n')
		tn.read_until(b'Password: ', 8)
		tn.write(passwordEnable.encode('utf-8') + b'\n')
		tn.read_until(b'#', 8)
		print("Telnet: Modo Enable habilitado.")
	"""except :
		print("Error con la Conexión")
		return None"""
	return tn


def obtener_subredes_telnet(tn):
	routeTable = b""
	#Expresion regular de una subred
	patron = re.compile('\\d{1,3}\\.\\d{1,3}\\.\\d{1,3}\\.\\d{1,3}/\\d{1,2}')
	tn.write(b'show ip route list subnets | exclude L        \n')
	while True:
		routeTable += tn.read_until(b' --More-- ', 1)
		if routeTable.find(b" --More-- ") != -1:
			routeTable = routeTable.replace(b" --More-- ", b"")
			tn.write(b' ')
			continue
		break
	#considerar >
	routeTable = routeTable.decode('utf8')
	return set(patron.findall(routeTable))


def obtener_subredes_tftp(tn, direccionServidorTFTP):
	patron = re.compile('\\d{1,3}\\.\\d{1,3}\\.\\d{1,3}\\.\\d{1,3}/\\d{1,2}')
	tn.write(b'show ip route list subnets | redirect tftp://192.168.0.2/tabla_routeo\n')
	tn.read_until(b'#', 8)
	fin = open("/srv/tftp/tabla_routeo", "rt")
	routeTable = fin.read()
	fin.close()
	subnets = set(patron.findall(routeTable))
	subnetsRes = []
	for subnet in subnets:
		if subnet.find("/32") == -1:
			subnetsRes.append(subnet)
	return subnetsRes


def intIp_to_string(ip):
	strIp = str((ip >> 24) & 255)
	strIp += '.' + str((ip >> 16) & 255)
	strIp += '.' + str((ip >> 8) & 255)
	strIp += '.' + str(ip & 255)
	return strIp


def info_subred(cidr):
	aux = cidr.split('/')
	subnet = aux[0].split('.')

	idSubred = 0 | int(subnet[0])
	idSubred = (idSubred << 8) | int(subnet[1])
	idSubred = (idSubred << 8) | int(subnet[2])
	idSubred = (idSubred << 8) | int(subnet[3])
	mascaraSubred = (~0) << (32 - int(aux[1]))
	broadcast =  (idSubred | (~mascaraSubred))
	
	strIdSubred = intIp_to_string(idSubred)
	strMascaraSubred = intIp_to_string(mascaraSubred)
	strBroadcast = intIp_to_string(broadcast)
	
	#Obtener todos los host de la subred
	listHosts = []
	host = idSubred + 1
	while host < broadcast:
		listHosts.append(intIp_to_string(host))
		host += 1

	return strIdSubred, strMascaraSubred, strBroadcast, listHosts


def ping_thread(subnet, red):
	strIdSubred, strMascaraSubred, strBroadcast, listHosts = info_subred(subnet)
	subred = ET.SubElement(red, 'subred')
	subred.set('id', strIdSubred)
	subred.set('mascara', strMascaraSubred)
	subred.set('broadcast', strBroadcast)
	for host in listHosts:
		command = ['ping', '-c', '1', '-W', '1', host]
		if subprocess.call(command) == 0:
			nodoHost = ET.SubElement(subred, 'host')
			nodoHost.text = host


def ping_puller(subnets):
	red = ET.Element('red')
	threads = list()
	for subnet in subnets:
		t = threading.Thread(target = ping_thread, args = (subnet, red,))
		threads.append(t)
		t.start()

	for t in threads:
		t.join()
	data = ET.tostring(red)
	file = open("ping_puller.xml", "w")
	file.write(data.decode('utf8'))


routerIP = '192.168.0.1'
ipServidorTFTP = '192.168.0.2'
passwordRouter = '1234'

#Conectar Telnet
tn = conectar_telnet(routerIP, passwordRouter, '1234')
subnets = obtener_subredes_telnet(tn)
subnets = obtener_subredes_tftp(tn, ipServidorTFTP)
tn.close()
print("Telnet: Conexión con " + routerIP + " cerrada.")

#Descubrir red
ping_puller(subnets)

for subnet in subnets:
	print("subred: " + subnet)