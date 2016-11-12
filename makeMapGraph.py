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

coordinates = json.load(open('fileForGraphic', 'r'))

x, y = map(coordinates['longitudes'], coordinates['latitudes'])

map.plot(x, y, 
	marker='D', markerfacecolor='m', markersize=6,
	color='cyan', linewidth=4
	)

filename = "foo.pdf"
if len(sys.argv)>1:
	filename = sys.argv[1] + ".pdf"

plt.savefig(filename, bbox_inches='tight')
# plt.show()