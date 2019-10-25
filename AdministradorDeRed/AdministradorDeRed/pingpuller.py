from queue import Queue
import subprocess  # For executing a shell command
import threading
import json
import os


class Subred:
	idSubred = 0
	strIdSubred = ''
	strMascara = ''
	strBroadcast = ''
	hosts = []

	def __init__(self, idSubred, strIdSubred, strMascara, strBroadcast):
		self.idSubred = idSubred
		self.strIdSubred = strIdSubred
		self.strMascara = strMascara
		self.strBroadcast = strBroadcast
		self.hosts = []

	def addHost(self, host):
		self.hosts.append(host)

	def formatoJson(self, data):
		hostData = []
		for host in self.hosts:
			hostData.append(host)

		data['subred'].append({
			'id': self.strIdSubred,
			'mascara' : self.strMascara,
			'broadcast': self.strBroadcast,
			'host' : hostData
		})


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
	broadcast = (idSubred | (~mascaraSubred))
	
	strIdSubred = intIp_to_string(idSubred)
	strMascaraSubred = intIp_to_string(mascaraSubred)
	strBroadcast = intIp_to_string(broadcast)
	
	#Obtener todos los host de la subred
	listHosts = []
	host = idSubred + 1

	""""
	while host < broadcast:
		listHosts.append(intIp_to_string(host))
		host += 1
	"""
	n = 0
	while n < 3:
		listHosts.append(intIp_to_string(host))
		host += 1
		n += 1

	return idSubred, strIdSubred, strMascaraSubred, strBroadcast, listHosts


def ping_thread(subnet):
	#Obtener informacion de la subred
	idSubred, strIdSubred, strMascaraSubred, strBroadcast, listHosts = info_subred(subnet)
	subred = Subred(idSubred, strIdSubred, strMascaraSubred, strBroadcast)
	for host in listHosts:
		#Ejecutar pings a la subred	
		FNULL = open(os.devnull, 'w')
		command = ['ping', '-c', '1', '-W', '3', host]
		if subprocess.call(command, stdout = FNULL, stderr = subprocess.STDOUT) == 0:
			#print(host + ' conectado')
			subred.addHost(host)
		#else:
			#print(host + ' no accesible')
	return subred


def ping_puller(subnets):
	threads = list()
	current_threads = 0
	total_treads = 0
	q = Queue()
	subredes = []

	for subnet in subnets:
		current_threads += 1
		total_treads += 1
		print("leyendo subred: " + subnet + ". current_thread: " + str(total_treads))
		#Ejecutar hilos para realizar los pings a las subredes
		t = threading.Thread(target = lambda q, arg1: q.put(ping_thread(arg1)), args = (q, subnet))
		threads.append(t)
		t.start()
		if current_threads == 10 or total_treads == len(subnets):
			current_threads = 0
			for t in threads:
				t.join()
			while not q.empty():
				subredes.append(q.get())
			threads.clear()
			q = Queue()

	return subredes


def getJsonPingPuller(subnets):
	data = {}
	data['subred'] = []
	subredes = ping_puller(subnets)
	#Ordenar Subredes
	for i in range(1,len(subredes)):
		for j in range(0,len(subredes)-i):
			if subredes[j].idSubred > subredes[j+1].idSubred:
				temp = subredes[j]
				subredes[j] = subredes[j+1]
				subredes[j+1] = temp

	for subred in subredes:
		subred.formatoJson(data)
	return json.dumps(data)

"""
tn, mssg = conectar_telnet('192.168.0.1', '1234', '1234')
if tn != None:
	subnets = obtener_subredes_telnet(tn)
	subredes = ping_puller(subnets)
	print(subredes)
	tn.close()
"""
