from scapy.all import *
from enum import Enum
import sys
import math


class PacketType(Enum):
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
		

	def Show(self):
		print "ip: " + str(self.ip)
		print "ttl: " + str(self.ttl)
		print "rttprom: " + str(self.rttprom)
		print "rtt list: " + str(self.rttlist)



def HuboRespuesta(hop):
	if hop.ip not 0:
		return true
	else
		return false


def CalcularRuta(host, ttl):
	ruta = []

	for ttl in range(1, 50):
		hop = Hop()

		for rafaga in range(1, 3):
			packet = IP(dst=host, ttl=ttl) / ICMP()
			ans, unans = sr(packet, timeout=10)

			if len(ans) != 0: #hubo respuesta
				packet_sent = ans[0][0]
				answer = ans[0][1]

				if (answer.type == PacketType.EchoReply): #Llegue al host
					rtt = (answer.time - packet_sent.sent_time)
					hop.ip = answer.src
					hop.rttlist.append(rtt)
					break

				if (answer.type == PacketType.TimeExceeded): #No llegue. Saco los datos host que me devolvio este paquete ICMP
					rtt = (answer.time - packet_sent.sent_time)
					hop.ip = answer.src 	#SERIOUS SHIT: PREGUNTAR QUE PASA SI TENGO VARIAS RUTAS DISTINTAS. ¿CON CUAL ME QUEDO?
					hop.rttlist.append(rtt)
		#end for

		if HuboRespuesta(hop):
			hop.rttprom = sum(hop.rttlist)/len(hop.rttlist)
			#.... aca hay que meterle al hop toda la gilada de geolocalizacion. Por ahi habria que llamar a esas paginas de geolocalizacion
			#desde el codigo y parsear lo que devuelven, para que quede todo automatico.
			#despues le agregamos esos campos a la clase hop y lo guardamos ahi.
			ruta.append(hop)

			if hop.ip == host:
				break

	#end for
	return ruta





if __name__ == '__main__':
