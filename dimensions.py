import sys
import requests
from requests.utils import quote
import overpass
from shapely.geometry import Polygon, Point
from shapely.ops import transform
import shapely.wkt
from rasterstats import zonal_stats
from osgeo import ogr
import pyproj
import cv2
import requests
import numpy
import math


class GIS:
    wgs84 = pyproj.CRS("EPSG:4326")
    osgb36 = pyproj.CRS("EPSG:27700")
    project = pyproj.Transformer.from_crs(wgs84, osgb36, always_xy=True).transform

    @staticmethod
    def reproject(geom):
        return transform(GIS.project, geom)

    @staticmethod
    def getBoundingBox(geom):
        return geom.minimum_rotated_rectangle


class OSM:
    radius = 5

    def getBuildingPolygon(self, lat, lng):
        api = overpass.API()
        response = api.get("""way["building"](around:%s, %s, %s)""" % (self.radius, lat, lng), verbosity="geom")
        if len(response.features) < 1:
            return None
        return GIS.reproject(Polygon(response.features[0].geometry.coordinates))

    @staticmethod
    def getNearestRoad(lat, lng):
        r = requests.get(url="""http://router.project-osrm.org/nearest/v1/driving/%s,%s""" % (lng, lat),
                         headers={"User-Agent": "curl/7.61.0"})

        if r.status_code == 200:
            road = r.json()
            road_location = road.get("waypoints")[0].get("location")
            point = Point(road_location)
            return GIS.reproject(point)
        else:
            return None


class Google:
    apiKey = "AIzaSyD4XzpPLesutnm9k0ZVZ-OCugAVHmqe58c"
    imageSize = 640
    zoom = 21

    def getPointLatLng(self, lat, lng, x, y):
        # print("getPointLatLng", lat, lng)
        parallelMultiplier = math.cos(lat * math.pi / 180)
        degreesPerPixelX = 360 / math.pow(2, self.zoom + 8)
        degreesPerPixelY = 360 / math.pow(2, self.zoom + 8) * parallelMultiplier
        pointLat = lat - degreesPerPixelY * (y - self.imageSize / 2)
        pointLng = lng + degreesPerPixelX * (x - self.imageSize / 2)
        return (pointLng, pointLat)

    def getBuildingPolygon(self, lat, lng):
        url = "http://maps.googleapis.com/maps/api/staticmap?center=%s,%s&zoom=%s&format=png32&size=%sx%s&maptype=roadmap&style=visibility:off&style=%s&key=%s" % (
            lat, lng, self.zoom, self.imageSize, self.imageSize,
            quote('feature:landscape.man_made|element:geometry.stroke|visibility:on|color:0xffffff|weight:1'),
            self.apiKey)

        resp = requests.get(url, stream=True).raw
        im = numpy.asarray(bytearray(resp.read()), dtype="uint8")
        im = cv2.imdecode(im, cv2.IMREAD_COLOR)
        imgray = cv2.cvtColor(im, cv2.COLOR_RGB2GRAY)
        ret, thresh = cv2.threshold(imgray, 127, 255, 0)
        contours, _ = cv2.findContours(thresh, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

        min_distance = sys.maxsize
        contour_idx = -1

        for idx, contour in enumerate(contours):
            distance = cv2.pointPolygonTest(contour, (self.imageSize / 2, self.imageSize / 2), True)
            if distance > 0 and distance < min_distance:
                min_distance = distance
                contour_idx = idx

        if contour_idx > -1:
            points = cv2.approxPolyDP(contours[contour_idx], 0.1 * cv2.arcLength(contour, True), True)
            coordinates = []
            for point in points:
                coordinates.append(self.getPointLatLng(lat, lng, point[0][0], point[0][1]))
            coordinates.append(coordinates[0])
            return GIS.reproject(Polygon(coordinates))
        else:
            return None


class DSM:
    raster = r"data/DTM-DSM.tif"

    @staticmethod
    def getHeight(box):
        stats = zonal_stats(box, DSM.raster)
        return stats[0].get("max")


class Property:
    def __init__(self, method):
        self.method = method

    def calculate_dimensions(self, road, lat, lng):
        poly = self.method.getBuildingPolygon(lat, lng)
        if poly is None:
            print("no building found")
        else:
            area = poly.area

            box = GIS.getBoundingBox(poly)
            x, y = box.exterior.coords.xy

            if road is not None:

                distances = (road.distance(Point(x[0], y[0])), road.distance(Point(x[1], y[1])),
                             road.distance(Point(x[2], y[2])), road.distance(Point(x[3], y[3])))

                index = distances.index(min(distances))

                if index == 0 or index == 2:
                    width = Point(x[0], y[0]).distance(Point(x[1], y[1]))
                    depth = Point(x[1], y[1]).distance(Point(x[2], y[2]))
                else:
                    width = Point(x[1], y[1]).distance(Point(x[2], y[2]))
                    depth = Point(x[0], y[0]).distance(Point(x[1], y[1]))
            else:

                print("error: couldn't snap to nearest road")

                edge_length = (
                    Point(x[0], y[0]).distance(Point(x[1], y[1])), Point(x[1], y[1]).distance(Point(x[2], y[2])))
                width = min(edge_length)
                depth = max(edge_length)

            height = DSM.getHeight(poly)
            # print(type(self.method).__name__)
            return width, depth, height, area


class Plot:
    file = r"data/Barnet.gml"

    def getPlot(self, lat, lng):
        source = ogr.Open(self.file)
        layer = source.GetLayer()
        point = GIS.reproject(Point(lng, lat))

        while True:
            feat = layer.GetNextFeature()
            if feat is None:
                break
            geom = feat.GetGeometryRef()
            wkt = geom.ExportToWkt()
            poly = shapely.wkt.loads(wkt)
            within = point.within(poly)
            if within:
                return poly

        return None

    def calculate_dimensions(self, road, lat, lng):

        plot = self.getPlot(lat, lng)

        if plot is not None:

            box = GIS.getBoundingBox(plot)
            x, y = box.exterior.coords.xy

            if road is not None:

                distances = (road.distance(Point(x[0], y[0])), road.distance(Point(x[1], y[1])),
                             road.distance(Point(x[2], y[2])), road.distance(Point(x[3], y[3])))

                index = distances.index(min(distances))

                if index == 0 or index == 2:
                    width = Point(x[0], y[0]).distance(Point(x[1], y[1]))
                    depth = Point(x[1], y[1]).distance(Point(x[2], y[2]))
                else:
                    width = Point(x[1], y[1]).distance(Point(x[2], y[2]))
                    depth = Point(x[0], y[0]).distance(Point(x[1], y[1]))
            else:

                print("error: couldn't snap to nearest road")

                edge_length = (
                    Point(x[0], y[0]).distance(Point(x[1], y[1])), Point(x[1], y[1]).distance(Point(x[2], y[2])))
                width = min(edge_length)
                depth = max(edge_length)

            return width, depth, plot.area

        else:
            print("plot not found")


if len(sys.argv) != 3:
    print("usage: dimensions.py lat lng")
    exit(1)

try:
    # lat = 51.581264
    # lng = -0.230575

    lat = float(sys.argv[1])
    lng = float(sys.argv[2])

    road = OSM.getNearestRoad(lat, lng)

    p = Plot()
    width, depth, plot_area = p.calculate_dimensions(road, lat, lng)

    print("plot width", width)
    print("plot depth", depth)
    print("plot area", plot_area)

    p = Property(OSM())
    width, depth, height, property_area = p.calculate_dimensions(road, lat, lng)

    print("OSM")
    print("property width", width)
    print("property depth", depth)
    print("property height", height)
    print("property area", property_area)
    print("land area", plot_area - property_area)
    
    p = Property(Google())
    width, depth, height, property_area = p.calculate_dimensions(road, lat, lng)

    print("Google")
    print("property width", width)
    print("property depth", depth)
    print("property height", height)
    print("property area", property_area)
    print("land area", plot_area - property_area)


except ValueError:
    print("params should be numbers")
    exit()

except:
    print("something went wrong")
    exit()
