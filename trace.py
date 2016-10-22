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




def calcularRuta(host, ttl):
	ruta = []

	for ttl in range(1, 50):
		hop = Hop()

		for rafaga in range(1, 10):
			ans, unans = sr(IP(dst=host, ttl=ttl) / ICMP(), timeout=10)

			if len(ans) != 0:
				packet_sent = ans[0][0]
				answer = ans[0][1]

				if (answer.type == PacketType.TimeExceeded):
					rtt = (answer.time - packet_sent.sent_time)
					hop.rttlist.append(rtt)



	return ruta





if __name__ == '__main__':
