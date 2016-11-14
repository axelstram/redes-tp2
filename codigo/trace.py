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
		self.esUnOutlier = False
		


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

		for rafaga in range(1, 10):
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
			hop.rttprom = numpy.average(hop.rttlist)
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
		hop.zrtt = abs(hop.deltaRTT-deltaRTTProm)/std



def guardarRTTRelativos(host, ruta):
	nombreArchivo = "rtt_relativos_" + str(host) + ".txt"
	nroHop = 1

	with io.FileIO(nombreArchivo, "w") as file:
		for hop in ruta:
			line = str(nroHop) + " " + str(hop.deltaRTT) + "\n"
			nroHop += 1
			file.write(line)


def guardarZRTT(host, ruta):
	nombreArchivo = "zrtt_" + str(host) + ".txt"
	nroHop = 1

	with io.FileIO(nombreArchivo, "w") as file:
		for hop in ruta:
			line = str(nroHop) + " " + str(hop.zrtt) + "\n"
			nroHop += 1
			file.write(line)


def modifiedThompsonTau(n):
	alpha = 0.05
	tStudent = t.ppf(1 - (alpha/2), df=n-2)
	return (tStudent*(n-1)) / (math.sqrt(n)*(math.sqrt(n-2+(tStudent**2))))



def esUnOutlier(deltaHopActual, tau, std):
	if deltaHopActual > tau*std:
		return True
	else:
		return False


def hallarHopOutlier(ruta, delta):
	for hop in ruta:
		if hop.deltaRTT == delta:
			return hop


def actualizarHop(hopNuevo, ruta):
	for hopOriginal in ruta:
		if hopOriginal.ip == hopNuevo.ip:
			hopOriginal.zrtt = hopNuevo.zrtt
			hopOriginal.esUnOutlier = hopNuevo.esUnOutlier



def calcularOutliers(ruta):
	outliers = []
	rutaOriginal = list(ruta)

	while len(ruta) > 2:
		deltaRTTList = [hop.deltaRTT for hop in ruta]
		deltaRTTProm = numpy.average(deltaRTTList)
		std = numpy.std(deltaRTTList)
		tau = modifiedThompsonTau(len(deltaRTTList))
		hayOutliers = ""

		for delta in deltaRTTList:
			deltaHopActual = abs(delta - deltaRTTProm)

			#print "deltaHopActual: " + str(deltaHopActual) + " tau: " + str(tau) + " std: " + str(std)

			if esUnOutlier(deltaHopActual, tau, std):
				hopOutlier = hallarHopOutlier(ruta, delta)
				hopOutlier.zrtt = deltaHopActual/std
				hopOutlier.esUnOutlier = True
				ruta = [otrosHops for otrosHops in ruta if otrosHops.ip != hopOutlier.ip]
				outliers.append(hopOutlier)
				hayOutliers = True

				print "Hop " + str(hopOutlier.ip) + " es un outlier con zrtt: " + str(hopOutlier.zrtt)

				break

			hayOutliers = False		
		#end for
		
		if not hayOutliers:
			if len(outliers) == 0:
				print "no hay outliers"
			else:
				print "no hay MAS outliers"

			break
	#end while
	
	rutaSinOutliers = ruta
	calcularZRTTParaCadaHop(rutaSinOutliers) #calculo todos los zrtt que me faltan. 

	#Actualizo todo en la ruta original. Es un asco pero no lo voy a hacer en O(n).
	for hop in rutaSinOutliers:
		actualizarHop(hop, rutaOriginal)

	for hop in outliers:
		actualizarHop(hop, rutaOriginal)


	for hop in rutaSinOutliers:
		print str(hop.ip) + " " + str(hop.deltaRTT) + " " + str(hop.zrtt)

	for hop in outliers:
	 	print str(hop.ip) + " " + str(hop.deltaRTT) + " " + str(hop.zrtt)


	return rutaOriginal



def outputFileForMap(ruta):
	fileForGraphic = open('fileForGraphic', 'w')

	coordinates = {'latitudes': [], 'longitudes': []}

	for hop in ruta:
		coordinates['latitudes'].append(hop.latitud)
		coordinates['longitudes'].append(hop.longitud)

	json.dump(coordinates, fileForGraphic)

	fileForGraphic.close()



def outputFileTable(ruta):
	fileForTable = open('fileForTable.tex', 'w')

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

	outputFileForMap(ruta)
	outputFileTable(ruta)
	
	ruta = calcularOutliers(ruta)
	print "Cantidad de hops en la ruta: " + str(len(ruta))

	if len(sys.argv) > 1:
		if sys.argv[2] == "1":
			guardarRTTRelativos(host, ruta)
			guardarZRTT(host, ruta)