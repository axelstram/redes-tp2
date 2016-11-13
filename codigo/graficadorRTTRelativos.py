import sys
import numpy as np
import matplotlib.pyplot as plt

def graficador(hops, rtts, imgName):
	rects1 = plt.plot(hops, rtts, color='red')

	plt.xlabel('hops')
	plt.ylabel('Rtt relativo (s)')

	#plt.ylim([-80,150])
	plt.title('Rtts entre saltos')
	#plt.xticks(hops+bar_width+0.4, hops)
	#plt.xticks(rotation = -75)
	plt.legend()
	plt.tight_layout()
	plt.savefig("graficos/rtts_entre_saltos_" + imgName)	
	plt.show()

if __name__ == "__main__":
	hops = []
	rtts = []
	with open(sys.argv[1]) as f:
		i = 0
		for line in f:
			if i!=0:
				print line
				line = line.split()
				hops.append(line[0])
				rtts.append(line[1])
			i = i+1

		rtts = [float(z) for z in rtts]
		imgName = sys.argv[2]
		graficador(hops, rtts, imgName)