from scapy.all import *
from scipy.stats import t
import sys
import math
import urllib2
import json
import socket
import io
import numpy
import matplotlib.pyplot as plt
from mpl_toolkits.basemap import Basemap


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


def calcularRuta(host, maxttl, burstsize):
	ruta = []
	hostIP = socket.gethostbyname(host)
	paquetesEnviados = 0
	paquetesNoRespondidos = 0

	for ttl in range(1, maxttl):
		hop = Hop()
		huboRespuesta = False

		for rafaga in range(1, burstsize):
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


def calcularOutliers(ruta):
	outliers = []

	while len(ruta) > 2:
		deltaRTTList = [hop.deltaRTT for hop in ruta]
		deltaRTTProm = numpy.average(deltaRTTList)
		std = numpy.std(deltaRTTList)
		tau = modifiedThompsonTau(len(deltaRTTList))
		hayOutliers = ""

		for delta in deltaRTTList:
			deltaHopActual = abs(delta - deltaRTTProm)

			#print "deltaRTTProm: " + str(deltaRTTProm)
			#print "deltaHopActual: " + str(deltaHopActual) + " tau: " + str(tau) + " std: " + str(std)

			if esUnOutlier(deltaHopActual, tau, std):
				hopOutlier = hallarHopOutlier(ruta, delta)
				ruta = [otrosHops for otrosHops in ruta if otrosHops != hopOutlier]
				outliers.append(hopOutlier)
				hayOutliers = True

				print "Hop " + str(hopOutlier.ip) + " es un outlier"
				break

			hayOutliers = False		
		#end for
		
		if not hayOutliers:
			if len(outliers) == 0:
				print "no hay outliers"
			else:
				print "no hay MAS outliers"

			break
		
			
	return outliers

def outputLatitudeLongitudeFile(ruta):
	fileForGraphic = open('fileForGraphic', 'w')

	coordinates = {'latitudes': [], 'longitudes': []}

	for hop in ruta:
		coordinates['latitudes'].append(hop.latitud)
		coordinates['longitudes'].append(hop.longitud)

	json.dump(coordinates, fileForGraphic)

	fileForGraphic.close()


def makeMapGraphic(ruta, filename):
	coordinates = {'latitudes': [], 'longitudes': []}

	for hop in ruta:
		coordinates['latitudes'].append(hop.latitud)
		coordinates['longitudes'].append(hop.longitud)

	# make sure the value of resolution is a lowercase L,
	#  for 'low', not a numeral 1
	map = Basemap(projection='robin', lat_0=0, lon_0=0)

	map.drawmapboundary(fill_color='black')
	map.drawcountries()
	map.fillcontinents(color='white',lake_color='black')
	map.drawcoastlines()

	x, y = map(coordinates['longitudes'], coordinates['latitudes'])

	map.plot(x, y, 
		marker='D', markerfacecolor='m', markersize=6,
		color='cyan', linewidth=4
		)

	filename += ".pdf"
	plt.savefig(filename, bbox_inches='tight')
	# plt.show()


def outputFileTable(ruta, filename):
	fileForTable = open(filename + ".tex", 'w')

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
	host = raw_input("Ingrese un host o IP: ")

	maxttl = raw_input("Ingrese el ttl hasta el que quiere ver: ")
	burstsize = raw_input("Ingrese el tamanio de cada rafaga: ")

	ruta = calcularRuta(host, int(maxttl), int(burstsize)) #ruta es la lista de hops

	calcularZRTTParaCadaHop(ruta)
	
	#MAPA
	makeMap = raw_input("Quiere crear el mapa? (s o n): ")
	if 's' in makeMap:
		mapName = raw_input("Ingrese un nombre para el mapa: ")
		makeMapGraphic(ruta, mapName)
		print "Tarea finalizada \n"

	#COORDENADAS
	writeCoordenatesToFile = raw_input("Quiere guardar las coordenadas de los saltos en un archivo? (s o n): ")
	if 's' in writeCoordenatesToFile:
		coordanatesFilename = raw_input("Ingrese un nombre para el archivo: ")
		outputLatitudeLongitudeFile(ruta, coordanatesFilename)
		print "Tarea finalizada \n"

	#TABLA
	makeTable = raw_input("Quiere crear el archivo para la tabla? (s o n): ")
	if 's' in makeTable:
		tableName = raw_input("Ingrese un nombre para el archivo: ")
		outputFileTable(ruta, tableName)
		print "Tarea finalizada \n"
	
	#OUTLIERS
	showOutliers = raw_input("Quiere calcular los outliers? (s o n): ")
	if 's' in showOutliers:
		outliers = calcularOutliers(ruta)
		print "Cantidad de hops en la ruta: " + str(len(ruta))
		print "Tarea finalizada \n"

	#RTT RELATIVOS
	showRTTRel = raw_input("Quiere mostrar los RTT relativos? (s o n): ")
	if 's' in showRTTRel:
		mostrarRTTRelativos(host, ruta)
		print "Tarea finalizada \n"
