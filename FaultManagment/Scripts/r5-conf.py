import telnetlib
command = 'cd /srv/tftp'

HostAnfitrion = '192.168.0.2'.encode('utf-8')
HostR2 = '192.168.5.2'.encode('utf-8')
PasswordTelnetR2 = '1234'.encode('utf-8')
PasswordEnableR2 = '1234'.encode('utf-8')

#Conectar Telnet R1
tn = telnetlib.Telnet(HostR2)
tn.set_debuglevel(9)
tn.read_until(b'Password: ', 5)
tn.write(PasswordTelnetR2 + b'\n')

#Activar el modo enable en R1
tn.read_until(b'R5>', 5)
tn.write(b'enable\n')

tn.read_until(b'Password: ', 5)
tn.write(PasswordEnableR2 + b'\n')

#Obtener el archivo de configuracion
tn.read_until(b'R5#', 5)
tn.write(b'copy running-config tftp:\n')

tn.read_until(b'Address or name of remote host []? ', 5)
tn.write(HostAnfitrion + b'\n')

tn.read_until(b'Destination filename ', 5)
tn.write(b'running-config-r5\n')
tn.read_until(b'R5#', 10)


#Modificar archivo de configuracion
fin = open("/srv/tftp/running-config-r5", "rt")
data = fin.read()
data = data.replace('interface FastEthernet3/0\n no ip address\n shutdown', 'interface FastEthernet3/0\n ip address 192.168.23.1 255.255.255.0\n no shutdown')
data = data.replace('ip forward-protocol nd', 'router ospf 1\n redistribute static\n network 192.168.23.0 0.0.0.255 area 0\n!\nip forward-protocol nd')
#data = data.replace('no ip address\nshutdown', '!')
fin.close()

fin = open("/srv/tftp/modified-running-config-r5", "wt")
fin.write(data)
fin.close()


#Remplazar archivo de configuracion
tn.write(b'copy tftp: running-config\n')

tn.read_until(b'Address or name of remote host []? ', 5)
tn.write(HostAnfitrion + b'\n')

tn.read_until(b'Source filename []? ', 5)
tn.write(b'modified-running-config-r5\n')

tn.read_until(b'Destination filename ', 5)
tn.write(b'running-config\n')

tn.read_until(b'R5#', 10)
tn.close()

print('** Router 5 Configurado **')