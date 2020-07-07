import sys
<<<<<<< HEAD
from sys import exit
=======
import sys
>>>>>>> 2d8e8cb870b6981c003e838fb65bfba951444679
import requests
from requests.utils import quote
import overpass
from shapely.geometry import Polygon, Point, LineString
from shapely.ops import transform, linemerge, unary_union, polygonize
import shapely.wkt
from rasterstats import zonal_stats
from osgeo import ogr
import pyproj
import cv2
import requests
import numpy
import math
<<<<<<< HEAD
import pdb
=======
import cmath
>>>>>>> 2d8e8cb870b6981c003e838fb65bfba951444679


class GIS:
    wgs84 = pyproj.CRS("EPSG:4326")
    osgb36 = pyproj.CRS("EPSG:27700")
    project = pyproj.Transformer.from_crs(wgs84, osgb36, always_xy=True).transform

    # project_back = pyproj.Transformer.from_crs(osgb36, wgs84, always_xy=True).transform

    @staticmethod
    def reproject(geom):
        return transform(GIS.project, geom)

    # @staticmethod
    # def reproject_back(geom):
    # return transform(GIS.project_back, geom)

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
    raster = r"data/DTM-DSM-G.tif"

    @staticmethod
    def getHeight(box):
        stats = zonal_stats(box, DSM.raster)
        return stats[0].get("max")


class Property:
    def __init__(self, method):
        self.method = method

    def calculateDimensions(self, road, lat, lng):
        poly = self.method.getBuildingPolygon(lat, lng)
        if poly is None:
            print("no building found")
            return None, None, None, None
        else:
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

                edge_length = (
                    Point(x[0], y[0]).distance(Point(x[1], y[1])), Point(x[1], y[1]).distance(Point(x[2], y[2])))
                width = min(edge_length)
                depth = max(edge_length)

            height = DSM.getHeight(poly)
            # print(type(self.method).__name__)
            return poly, width, depth, height


class Plot:
    file = r"data/Barnet.gml"

    def getPlotPolygon(self, lat, lng):
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

    def calculateDimensions(self, road, lat, lng):

        poly = self.getPlotPolygon(lat, lng)

        if poly is not None:

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

                edge_length = (
                    Point(x[0], y[0]).distance(Point(x[1], y[1])), Point(x[1], y[1]).distance(Point(x[2], y[2])))
                width = min(edge_length)
                depth = max(edge_length)

            return poly, width, depth

        else:
            print("plot not found")
            return None, None, None


class RearGarden:

    def __init__(self, property, plot, road):
        self.property = property
        self.plot = plot
        self.road = road

    @staticmethod
    def pairs(lst):
        for i in range(1, len(lst)):
            yield lst[i - 1], lst[i]

    @staticmethod
    def extendLine(coords, dist):
        x1 = coords[0][0]
        y1 = coords[0][1]
        x2 = coords[1][0]
        y2 = coords[1][1]

        difference = complex(x2, y2) - complex(x1, y1)

        (distance, angle) = cmath.polar(difference)
        displacement = cmath.rect(dist, angle)
        xy3 = displacement + complex(x2, y2)
        x3 = xy3.real
        y3 = xy3.imag

        (distance, angle) = cmath.polar(-difference)
        displacement = cmath.rect(dist, angle)
        xy4 = displacement + complex(x1, y1)
        x4 = xy4.real
        y4 = xy4.imag

        return LineString([(x3, y3), (x4, y4)])

    def getFurthestWall(self):
        max_distance = 0
        for pair in self.pairs(list(self.property.exterior.coords)):
            line = LineString([pair[0], pair[1]])
            d = self.road.distance(line)
            if d > max_distance:
                max_distance = d
                max_line = line

        extended_line = self.extendLine(max_line.coords, 10)
        return extended_line

    def getRearGardenPolygon(self):
        wall = self.getFurthestWall()

        merged = linemerge([self.plot.boundary, wall])
        borders = unary_union(merged)
        polygons = polygonize(borders)

        max_distance = 0
        for p in polygons:
            d = self.road.distance(p)
            if d > max_distance:
                max_distance = d
                rear_garden = p

        return rear_garden

    def calculateDimensions(self):
        poly = self.getRearGardenPolygon()

        if poly is not None:

            box = GIS.getBoundingBox(poly)
            x, y = box.exterior.coords.xy

            if self.road is not None:

                distances = (self.road.distance(Point(x[0], y[0])), self.road.distance(Point(x[1], y[1])),
                             self.road.distance(Point(x[2], y[2])), self.road.distance(Point(x[3], y[3])))

                index = distances.index(min(distances))

                if index == 0 or index == 2:
                    width = Point(x[0], y[0]).distance(Point(x[1], y[1]))
                    depth = Point(x[1], y[1]).distance(Point(x[2], y[2]))
                else:
                    width = Point(x[1], y[1]).distance(Point(x[2], y[2]))
                    depth = Point(x[0], y[0]).distance(Point(x[1], y[1]))
            else:

                edge_length = (
                    Point(x[0], y[0]).distance(Point(x[1], y[1])), Point(x[1], y[1]).distance(Point(x[2], y[2])))
                width = min(edge_length)
                depth = max(edge_length)

            return poly, width, depth

        else:
            print("rear garden not found")
            return None, None, None


if len(sys.argv) != 3:
    print("usage: dimensions.py lat lng")
    exit(1)

try:
    # lat = 51.581264
    # lng = -0.230575

    lat = float(sys.argv[1])
    lng = float(sys.argv[2])

    road = OSM.getNearestRoad(lat, lng)
    if road is None:
        print("error: couldn't snap to nearest road")

<<<<<<< HEAD
    # p = Plot()
    # width, depth, plot_area = p.calculate_dimensions(road, lat, lng)
    #
    # print("plot width", width)
    # print("plot depth", depth)
    # print("plot area", plot_area)

    # p = Property(OSM())
    # width, depth, height, property_area = p.calculate_dimensions(road, lat, lng)
    #
    # print("OSM")
    # print("property width", width)
    # print("property depth", depth)
    # print("property height", height)
    # print("property area", property_area)
    # print("land area", plot_area - property_area)

    p = Property(Google())
    width, depth, height, property_area = p.calculate_dimensions(road, lat, lng)

    print("Google")
    print("property width", width)
    print("property depth", depth)
    print("property height", height)
    print("property area", property_area)
    print("land area", plot_area - property_area)
=======
    p = Plot()
    plot, width, depth = p.calculateDimensions(road, lat, lng)

    if plot is not None:

        plot_area = plot.area

        print("plot width", width)
        print("plot depth", depth)
        print("plot area", plot_area)
        print("")
        
        p = Property(OSM())
        property, width, depth, height = p.calculateDimensions(road, lat, lng)
        if property is not None:
            property_area = property.area

            rear = RearGarden(property, plot, road)
            rear_garden, rear_garden_width, rear_garden_depth = rear.calculateDimensions()

            if rear_garden is not None:
                rear_garden_area = rear_garden.area

            print("OSM")
            print("property width", width)
            print("property depth", depth)
            print("property height", height)

            print("rear garden width", rear_garden_width)
            print("rear garden depth", rear_garden_depth)

            print("property area", property_area)
            print("land area", plot_area - property_area)
            print("rear garden area", rear_garden_area);

            print("")

        p = Property(Google())
        property, width, depth, height = p.calculateDimensions(road, lat, lng)
        if property is not None:
            property_area = property.area

            rear = RearGarden(property, plot, road)
            rear_garden, rear_garden_width, rear_garden_depth = rear.calculateDimensions()

            if rear_garden is not None:
                rear_garden_area = rear_garden.area

            print("Google")
            print("property width", width)
            print("property depth", depth)
            print("property height", height)

            print("rear garden width", rear_garden_width)
            print("rear garden depth", rear_garden_depth)

            print("property area", property_area)
            print("land area", plot_area - property_area)
            print("rear garden area", rear_garden_area);
>>>>>>> 2d8e8cb870b6981c003e838fb65bfba951444679

            # print(GIS.reproject_back(plot.difference(property)))

except ValueError:
    print("params should be numbers")
    exit()

except:
    print("something went wrong")
    exit()
