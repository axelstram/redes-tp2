from scapy.all import *
import sys
import math



class Hop:
	def __init__(self):
		self.ip = 0
		self.ttl = 0
		self.rttprom = 0
		

	def Show(self):
		print "ip: "+str(self.ip)
		print "ttl: "+str(self.ttl)
		print "rttprom: "+str(self.rttprom)
		



def calcularRuta(host):
	ruta = []

	for i in range(1, 50):
		#otro for para mandar mas paquetes por cada ttl?
		answered, unanswered = sr(IP(dst=host, ttl=i) / ICMP(), timeout=10)
		

	return ruta


if __name__ == '__main__':
