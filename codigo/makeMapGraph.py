import sys
import matplotlib.pyplot as plt
from mpl_toolkits.basemap import Basemap
import numpy as np
import json
 
# make sure the value of resolution is a lowercase L,
#  for 'low', not a numeral 1
map = Basemap(projection='robin', lat_0=0, lon_0=0)

map.drawmapboundary(fill_color='black')
map.drawcountries()
map.fillcontinents(color='white',lake_color='black')
map.drawcoastlines()

inputFileName = "fileForGraphic"
if len(sys.argv)>1:
	inputFileName = sys.argv[1]

coordinates = json.load(open(inputFileName, 'r'))

x, y = map(coordinates['longitudes'], coordinates['latitudes'])

map.plot(x, y, 
	marker='D', markerfacecolor='m', markersize=6,
	color='cyan', linewidth=4
	)

outputFileName = inputFileName + ".pdf"
if len(sys.argv)>2:
	outputFileName = sys.argv[2] + ".pdf"

plt.savefig(outputFileName, bbox_inches='tight')
# plt.show()