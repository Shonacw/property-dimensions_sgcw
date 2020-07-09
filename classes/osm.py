import sys
import overpass
import requests
from shapely.geometry import Polygon, Point

from .gis import GIS
from .property import Property


class OSM:
    @staticmethod
    def getNearestRoad(lat, lng):
        r = requests.get(url="""http://router.project-osrm.org/nearest/v1/driving/%s,%s""" % (lng, lat),
                         headers={"User-Agent": "curl/7.61.0"})

        if r.status_code == 200:
            road = r.json()
            name = road.get("waypoints")[0].get("name")
            if name == "":
                return None
            else:
                road_location = road.get("waypoints")[0].get("location")
                point = Point(road_location)
                #print("snapped to nearest road using osrm")
                return GIS.reprojectToOSGB36(point)
        else:
            return None


class OSMProperty(Property):
    radius = 5

    def findPolygon(self):
        api = overpass.API()
        response = api.get("""way["building"](around:%s, %s, %s)""" % (self.radius, self.lat, self.lng),
                           verbosity="geom")
        if len(response.features) < 1:
            return None
        elif len(response.features) > 1:
            point = GIS.reprojectToOSGB36(Point(self.lng, self.lat))
            minDistance = sys.maxsize
            for feature in response.features:
                poly = GIS.reprojectToOSGB36(Polygon(feature.geometry.coordinates))
                distance = poly.distance(point)
                if distance < minDistance:
                    minDistance = distance
                    nearestFeature = poly
            return nearestFeature
        else:
            return GIS.reprojectToOSGB36(Polygon(response.features[0].geometry.coordinates))
