import telnetlib
command = 'cd /srv/tftp'

HostAnfitrion = '192.168.0.2'.encode('utf-8')
HostR1 = '192.168.0.1'.encode('utf-8')
PasswordTelnetR1 = '1234'.encode('utf-8')
PasswordEnableR1 = '1234'.encode('utf-8')

#Conectar Telnet R1
tn = telnetlib.Telnet(HostR1)
tn.set_debuglevel(9)
tn.read_until(b'Password: ', 5)
tn.write(PasswordTelnetR1 + b'\n')

#Activar el modo enable en R1
tn.read_until(b'R1>', 5)
tn.write(b'enable\n')

tn.read_until(b'Password: ', 5)
tn.write(PasswordEnableR1 + b'\n')

#Obtener el archivo de configuracion
tn.read_until(b'R1#', 5)
tn.write(b'copy running-config tftp:\n')

tn.read_until(b'Address or name of remote host []? ', 5)
tn.write(HostAnfitrion + b'\n')

tn.read_until(b'Destination filename ', 5)
tn.write(b'running-config-r1\n')
tn.read_until(b'R1#', 10)


#Modificar archivo de configuracion
fin = open("/srv/tftp/running-config-r1", "rt")
data = fin.read()
data = data.replace('interface FastEthernet2/0\n no ip address\n shutdown', 'interface FastEthernet2/0\n ip address 192.168.22.1 255.255.255.0\n no shutdown')
data = data.replace('ip forward-protocol nd', 'router ospf 1\n redistribute static\n network 192.168.22.0 0.0.0.255 area 0\n!\nip forward-protocol nd')
#data = data.replace('no ip address\nshutdown', '!')
fin.close()

fin = open("/srv/tftp/modified-running-config-r1", "wt")
fin.write(data)
fin.close()


#Remplazar archivo de configuracion
tn.write(b'copy tftp: running-config\n')

tn.read_until(b'Address or name of remote host []? ', 5)
tn.write(HostAnfitrion + b'\n')

tn.read_until(b'Source filename []? ', 5)
tn.write(b'modified-running-config-r1\n')

tn.read_until(b'Destination filename ', 5)
tn.write(b'running-config\n')

tn.read_until(b'R1#', 10)
tn.close()

print('** Router 1 Configurado **')