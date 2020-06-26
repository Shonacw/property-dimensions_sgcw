import sys
import overpass
from shapely.geometry import Polygon, Point
from shapely.ops import transform
from rasterstats import zonal_stats
import pyproj
import requests

raster = r"data/DTM-DSM.tif"

if len(sys.argv) != 3:
    print("usage: osm.py lat lng")
    exit(1)

lat = sys.argv[1]
lng = sys.argv[2]

wgs84 = pyproj.CRS("EPSG:4326")
osgb36 = pyproj.CRS("EPSG:27700")
project = pyproj.Transformer.from_crs(wgs84, osgb36, always_xy=True).transform

api = overpass.API()
response = api.get("""way["building"](around:10, %s, %s)""" % (lat, lng), verbosity="geom")

if len(response.features) < 1:
    print("no building found")
    exit(1)

coordinates = response.features[0].geometry.coordinates

poly = Polygon(coordinates)
projected_poly = transform(project, poly)

box = projected_poly.minimum_rotated_rectangle

r = requests.get(url="""http://router.project-osrm.org/nearest/v1/driving/%s,%s""" % (lng, lat),
                 headers={"User-Agent": "curl/7.61.0"})

if r.status_code == 200:

    road = r.json()
    road_location = road.get("waypoints")[0].get("location")
    point = Point(road_location)
    projected_point = transform(project, point)
    # print(projected_point)

    x, y = box.exterior.coords.xy

    distances = (projected_point.distance(Point(x[0], y[0])), projected_point.distance(Point(x[1], y[1])),
                 projected_point.distance(Point(x[2], y[2])), projected_point.distance(Point(x[3], y[3])))

    index = distances.index(min(distances))

    if index == 0 or index == 2:
        width = Point(x[0], y[0]).distance(Point(x[1], y[1]))
        depth = Point(x[1], y[1]).distance(Point(x[2], y[2]))
    else:
        width = Point(x[1], y[1]).distance(Point(x[2], y[2]))
        depth = Point(x[0], y[0]).distance(Point(x[1], y[1]))

else:

    print("error: couldn't snap to nearest road")
    box = projected_poly.minimum_rotated_rectangle
    x, y = box.exterior.coords.xy
    edge_length = (Point(x[0], y[0]).distance(Point(x[1], y[1])), Point(x[1], y[1]).distance(Point(x[2], y[2])))
    width = min(edge_length)
    depth = max(edge_length)

stats = zonal_stats(projected_poly, raster)

print("property depth", depth)
print("property width", width)
print("property height", stats[0].get("max"))
print("property area", projected_poly.area)
