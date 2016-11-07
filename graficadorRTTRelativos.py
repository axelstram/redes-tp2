import sys
import numpy as np
import matplotlib.pyplot as plt

def graficador(ips,rtts):
	print len(ips)
	print len(rtts)

	n = len(ips)
	index = np.arange(n)

	bar_width = 0.8
	opacity = 0.4

	rects1 = plt.bar(index, rtts, alpha=opacity, color='red')

	plt.xlabel('Direcciones de IP')
	plt.ylabel('Rtt relativo')

	plt.ylim([-80,150])
	plt.title('Rtts relativos x IP')
	plt.xticks(index+bar_width+0.4, ips)
	plt.xticks(rotation = -75)
	plt.legend()
	plt.tight_layout()
	plt.savefig("graficos/rttsRelativos")	
	plt.show()

if __name__ == "__main__":
	ips = []
	rtts = []
	with open(sys.argv[1]) as f:
		i = 0
		for line in f:
			if i!=0:
				line = line.split()
				print line
				ips.append(line[0])
				rtts.append(line[1])
			i = i+1

		rtts = [float(z) for z in rtts]
		#graficador(ips,rtts)