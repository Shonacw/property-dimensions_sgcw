import sys
import overpass
from shapely.geometry import Polygon, Point
from shapely.ops import transform
from rasterstats import zonal_stats
import pyproj

raster = r"data/DTM-DSM.tif"

if len(sys.argv) != 3:
    print('usage: osm.py lat lng')
    exit(1)

lat = sys.argv[1]
lng = sys.argv[2]

wgs84 = pyproj.CRS('EPSG:4326')
osgb36 = pyproj.CRS('EPSG:27700')
project = pyproj.Transformer.from_crs(wgs84, osgb36, always_xy=True).transform

api = overpass.API()
response = api.get("""way["building"](around:5, %s, %s)""" % (lat, lng), verbosity='geom')

if len(response.features) < 1:
    print('no building found')
    exit(1)

coordinates = response.features[0].geometry.coordinates

poly = Polygon(coordinates)
projected_poly = transform(project, poly)
print(projected_poly.area)

box = projected_poly.minimum_rotated_rectangle
x, y = box.exterior.coords.xy
edge_length = (Point(x[0], y[0]).distance(Point(x[1], y[1])), Point(x[1], y[1]).distance(Point(x[2], y[2])))

depth = max(edge_length)
print(depth)

width = min(edge_length)
print(width)

stats = zonal_stats(projected_poly, raster)
print(stats[0].get("max"))
