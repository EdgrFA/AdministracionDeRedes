sudo tunctl -t tap1 -u edgrfa
sudo ifconfig tap1 up
sudo ifconfig tap1 192.168.28.2 netmask 255.255.255.0 up
sudo route add -net 192.168.0.0 gw 192.168.28.1 netmask 255.255.255.0 dev tap1
sudo route add -net 192.168.1.0 gw 192.168.28.1 netmask 255.255.255.0 dev tap1
sudo route add -net 192.168.2.0 gw 192.168.28.1 netmask 255.255.255.0 dev tap1
sudo route add -net 192.168.3.0 gw 192.168.28.1 netmask 255.255.255.0 dev tap1
sudo route add -net 192.168.4.0 gw 192.168.28.1 netmask 255.255.255.0 dev tap1
sudo route add -net 192.168.5.0 gw 192.168.28.1 netmask 255.255.255.0 dev tap1
sudo route add -net 192.168.6.0 gw 192.168.28.1 netmask 255.255.255.0 dev tap1
sudo route add -net 192.168.7.0 gw 192.168.28.1 netmask 255.255.255.0 dev tap1
sudo route add -net 192.168.8.0 gw 192.168.28.1 netmask 255.255.255.0 dev tap1
sudo route add -net 192.168.9.0 gw 192.168.28.1 netmask 255.255.255.0 dev tap1
sudo route add -net 192.168.10.0 gw 192.168.28.1 netmask 255.255.255.0 dev tap1
sudo route add -net 192.168.11.0 gw 192.168.28.1 netmask 255.255.255.0 dev tap1
sudo route add -net 192.168.12.0 gw 192.168.28.1 netmask 255.255.255.0 dev tap1
sudo route add -net 192.168.13.0 gw 192.168.28.1 netmask 255.255.255.0 dev tap1
sudo route add -net 192.168.14.0 gw 192.168.28.1 netmask 255.255.255.0 dev tap1
sudo route add -net 192.168.15.0 gw 192.168.28.1 netmask 255.255.255.0 dev tap1
sudo route add -net 192.168.16.0 gw 192.168.28.1 netmask 255.255.255.0 dev tap1
sudo route add -net 192.168.17.0 gw 192.168.28.1 netmask 255.255.255.0 dev tap1
sudo route add -net 192.168.18.0 gw 192.168.28.1 netmask 255.255.255.0 dev tap1
sudo route add -net 192.168.19.0 gw 192.168.28.1 netmask 255.255.255.0 dev tap1
sudo route add -net 192.168.20.0 gw 192.168.28.1 netmask 255.255.255.0 dev tap1
sudo route add -net 192.168.21.0 gw 192.168.28.1 netmask 255.255.255.0 dev tap1
sudo route add -net 192.168.22.0 gw 192.168.28.1 netmask 255.255.255.0 dev tap1
sudo route add -net 192.168.23.0 gw 192.168.28.1 netmask 255.255.255.0 dev tap1
sudo route add -net 192.168.24.0 gw 192.168.28.1 netmask 255.255.255.0 dev tap1
sudo route add -net 192.168.25.0 gw 192.168.28.1 netmask 255.255.255.0 dev tap1
sudo route add -net 192.168.26.0 gw 192.168.28.1 netmask 255.255.255.0 dev tap1
sudo route add -net 192.168.27.0 gw 192.168.28.1 netmask 255.255.255.0 dev tap1
