from scapy.all import *
from scipy.stats import t
import sys
import math
import urllib2
import json
import socket
import io
import numpy


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
		self.rttprom = 0.0
		self.rttlist = []
		self.deltaRTT = 0.0
		self.std = 0.0
		self.pais = ""
		self.ciudad = ""
		self.latitud = 0.0
		self.longitud = 0.0
		self.zrtt = 0.0
		

	def show(self):
		print "ip: " + str(self.ip)
		print "ttl: " + str(self.ttl)
		print "rttprom: " + str(self.rttprom)
		print "rtt list: " + str(self.rttlist)
		print "delta rtt: " + str(self.deltaRTT)
		print "std: " + str(self.std)
		print "pais: " + str(self.pais)
		print "ciudad: " + str(self.ciudad)
		print "latitud: " + str(self.latitud)
		print "longitud: " + str(self.longitud)
		print "zrtt: " + str(self.zrtt)



def geolocalizar(ip):
	dicc = json.loads(urllib2.urlopen("http://freegeoip.net/json/" + str(ip)).read())

	if dicc["country_name"] == "":
		dicc["country_name"] = "Argentina"
		dicc["city"] = "Buenos Aires"
		dicc["latitude"] = -34.6006
		dicc["longitude"] = -58.4887 

	print "\n" + ip + ", " + dicc["country_name"] + "\n"

	return dicc["country_name"], dicc["city"], dicc["latitude"], dicc["longitude"]

	#{u'city': u'Nunez', u'region_code': u'C', u'region_name': u'Buenos Aires F.D.', u'ip': u'181.167.161.118', 
	#u'time_zone': u'America/Argentina/Buenos_Aires', u'longitude': -58.4504, u'metro_code': 0, u'latitude': -34.5487, 
	#u'country_code': u'AR', u'country_name': u'Argentina', u'zip_code': u''}


def calcularRuta(host):
	ruta = []
	hostIP = socket.gethostbyname(host)
	paquetesEnviados = 0
	paquetesNoRespondidos = 0

	for ttl in range(1, 30):
		hop = Hop()
		huboRespuesta = False

		for rafaga in range(1, 6):
			packet = IP(dst=host, ttl=ttl) / ICMP()
			ans, unans = sr(packet, timeout=2)
			paquetesEnviados += 1

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

			if len(unans) != 0:
				paquetesNoRespondidos += 1
		#end for

		if huboRespuesta:
			hop.rttprom = sum(hop.rttlist)/len(hop.rttlist)
			pais, ciudad, latitud, longitud = geolocalizar(hop.ip)
			hop.pais = pais
			hop.ciudad = ciudad
			hop.latitud = latitud
			hop.longitud = longitud

			if len(ruta) == 0:
				hop.deltaRTT = hop.rttprom
			else:
				hop.deltaRTT = hop.rttprom - ruta[-1].rttprom

			if hop.deltaRTT < 0:
				hop.deltaRTT = 0

			hop.std = numpy.std(hop.rttlist)

			ruta.append(hop)

			if hop.ip == hostIP:
				print "Llego!!!"
				break
			
			
	#end for

	print "Paquetes enviados: " + str(paquetesEnviados) + " / Paquetes no respondidos: " + str(paquetesNoRespondidos)
	return ruta



def calcularZRTTParaCadaHop(ruta):
	deltaRTTList = [hop.deltaRTT for hop in ruta]
	deltaRTTProm = numpy.average(deltaRTTList)
	std = numpy.std(deltaRTTList)

	for hop in ruta:
		hop.zrtt = (hop.deltaRTT-deltaRTTProm)/std



def mostrarRTTRelativos(host, ruta):
	nombreArchivo = "rtt_relativos_" + str(host) + ".txt"
	nroHop = 1

	with io.FileIO(nombreArchivo, "w") as file:
		for hop in ruta:
			line = str(nroHop) + " " + str(hop.deltaRTT) + "\n"
			nroHop += 1
			file.write(line)



def modifiedThompsonTau(n):
	alpha = 0.05
	tStudent = t.pdf(alpha/2, df=n-2)
	print "t student: " + str(tStudent) + " n-2: " + str(n-2)
	return (tStudent*(n-1)) / (math.sqrt(n)*(math.sqrt(n-2+(tStudent**2))))



def hayOutliers(deltaHopActual, tau, std):
	if deltaHopActual > tau*std:
		return True
	else:
		return False



def calcularOutliers(ruta):
	outliers = []

	for hop in ruta:
		if len(ruta) <= 2:
			break

		deltaRTTList = [hop.deltaRTT for hop in ruta]
		deltaRTTProm = numpy.average(deltaRTTList)
		std = numpy.std(deltaRTTList)
		tau = modifiedThompsonTau(len(ruta))
		deltaHopActual = abs(hop.deltaRTT - deltaRTTProm)

		print "deltaHopActual: " + str(deltaHopActual) + " tau: " + str(tau) + " std: " + str(std)

		if hayOutliers(deltaHopActual, tau, std):
			ruta = [otrosHops for otrosHops in ruta if otrosHops != hop]
			outliers.append(hop)
			print "Hop " + str(hop.ip) + " es un outlier"
		else:
			#no hay outliers.
			break
			
	return outliers

def outputFileForMap(ruta):
	fileForGraphic = open('fileForGraphic', 'w')

	coordinates = {'latitudes': [], 'longitudes': []}

	for hop in ruta:
		coordinates['latitudes'].append(hop.latitud)
		coordinates['longitudes'].append(hop.longitud)

	json.dump(coordinates, fileForGraphic)

	fileForGraphic.close()

def outputFileTable(ruta):
	fileForTable = open('fileForTable', 'w')

	fileForTable.write('\\begin{tabular}{| l | c | c | c | c |}\n')
	fileForTable.write('\\hline\n')
	fileForTable.write('Hop & IP &  RTT promedio (s)  & deltaRTT promedio & Ubicacion\\\\ \n')
	fileForTable.write('\\hline\n')

	i = 1
	for hop in ruta:
		line = str(i) + " & " + str(hop.ip) + " & " + str(hop.rttprom)  + " & " + str(hop.deltaRTT) + " & " + hop.pais
		if hasattr(hop, 'ciudad') and hop.ciudad != "":
			line += ", " + hop.ciudad 
		fileForTable.write(line + '\\\\' + '\n')
		fileForTable.write('\\hline\n')
		i += 1

	fileForTable.write('\\end{tabular}')


#--------------------------------------------

if __name__ == '__main__':
	if sys.argv[1] == "":
		print "No se ingreso ningun host"
		exit(1)

	host = sys.argv[1]
	ruta = calcularRuta(host) #ruta es la lista de hops
	calcularZRTTParaCadaHop(ruta) 

	outputFileForMap(ruta)
	outputFileTable(ruta)
	
	#outliers = calcularOutliers(ruta)

	if len(sys.argv) > 1 and sys.argv[2] == "1":
			mostrarRTTRelativos(host, ruta)
