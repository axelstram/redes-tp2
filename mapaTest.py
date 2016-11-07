import matplotlib.pyplot as plt
from mpl_toolkits.basemap import Basemap
import numpy as np
 
# make sure the value of resolution is a lowercase L,
#  for 'low', not a numeral 1
map = Basemap(projection='robin', lat_0=0, lon_0=0)

map.drawmapboundary(fill_color='black')
map.fillcontinents(color='white',lake_color='black')
map.drawcoastlines()

lon = [0, 20, 45]
lat = [0, -20, 45]

x, y = map(lon, lat)

map.plot(x, y, 
	marker='D', markerfacecolor='m', 
	color='yellow', linewidth=2,
	linestyle=':'
	)

lineSize = 900000
for i in range(0, len(x)-1):
	d = ((x[i+1] - x[i]), (y[i+1] - y[i]))
	dLen = np.sqrt(d[0]*d[0] + d[1]*d[1])

	plt.arrow(
		x[i], y[i], 
		(d[0]/dLen)*lineSize, (d[1]/dLen)*lineSize, 
		linewidth=4, color='m')

plt.show()