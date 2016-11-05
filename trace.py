from scapy.all import *
import sys
import math
import urllib2
import json


class PacketType():
	EchoReply = 0
	DestUnreachable = 3
	SourceQuench = 4
	Redirect = 5
	AltHostAddress = 6
	Echo = 8
	RouterAdvertisement = 9
	RouterSelection = 10
	TimeExceeded = 11
	ParamProblem = 12
	Timestamp = 13
	TimestampReply = 14
	InfoRequest = 15
	InfoReply = 16
	AddressMaskRequest = 17
	AddressMaskReply = 18



class Hop:
	def __init__(self):
		self.ip = 0
		self.ttl = 0
		self.rttprom = 0
		self.rttlist = []
		self.pais = ""
		self.ciudad = ""
		self.latitud = 0.0
		self.longitud = 0.0
		

	def Show(self):
		print "ip: " + str(self.ip)
		print "ttl: " + str(self.ttl)
		print "rttprom: " + str(self.rttprom)
		print "rtt list: " + str(self.rttlist)
		print "pais: " + str(self.pais)
		print "ciudad: " + str(self.ciudad)
		print "latitud: " + str(self.latitud)
		print "longitud: " + str(self.longitud)


def Geolocalizar(ip):
	print ip
	dicc = json.loads(urllib2.urlopen("http://ip-api.com/json/" + ip).read())
	if "country" not in dicc.keys():
		dicc = json.loads(urllib2.urlopen("http://ip-api.com/json/").read()) #para que me devuelva la ubicacion mia.
	print dicc["country"]
	return [dicc["country"], dicc["city"], dicc["lat"], dicc["lon"]]


def CalcularRuta(host):
	ruta = []

	for ttl in range(10, 50):
		hop = Hop()
		huboRespuesta = False

		for rafaga in range(1, 2):
			packet = IP(dst=host, ttl=ttl) / ICMP()
			ans, unans = sr(packet, timeout=20)

			if len(ans) != 0:
				huboRespuesta = True
				packet_sent = ans[0][0]
				answer = ans[0][1]

				if (answer.type == PacketType.EchoReply): #Llegue al host
					rtt = (answer.time - packet_sent.sent_time)
					hop.ip = answer.src
					hop.rttlist.append(rtt)
					break

				if (answer.type == PacketType.TimeExceeded): #No llegue. Saco los datos host que me devolvio este paquete ICMP
					rtt = (answer.time - packet_sent.sent_time)
					hop.ip = answer.src
					hop.rttlist.append(rtt)
		#end for

		if huboRespuesta:
			hop.rttprom = sum(hop.rttlist)/len(hop.rttlist)
			pais_ciudad_latitud_longitud = Geolocalizar(hop.ip)
			hop.pais = pais_ciudad_latitud_longitud[0]
			hop.ciudad = pais_ciudad_latitud_longitud[1]
			hop.latitud = pais_ciudad_latitud_longitud[2]
			hop.longitud = pais_ciudad_latitud_longitud[3]

			ruta.append(hop)

			if hop.ip == host:
				break

	#end for
	return ruta





if __name__ == '__main__':
	ruta = CalcularRuta("www.google.com")