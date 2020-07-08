import sys
import math
import cv2
import numpy
import requests
from requests.utils import quote
from shapely.geometry import Polygon, Point

from .gis import GIS
from .property import Property

apiKey = "AIzaSyD4XzpPLesutnm9k0ZVZ-OCugAVHmqe58c"


class Google:
    @staticmethod
    def getNearestRoad(lat, lng):
        r = requests.get(
            url="""https://roads.googleapis.com/v1/nearestRoads?points=%s,%s&key=%s""" % (lat, lng, apiKey),
            headers={"User-Agent": "curl/7.61.0"})

        if r.status_code == 200:
            response = r.json()
            location = response.get("snappedPoints")[0].get("location")
            point = Point(location.get("longitude"), location.get("latitude"))
            print("snapped to nearest road using google roads api")
            return GIS.reprojectToOSGB36(point)
        else:
            return None


class GoogleProperty(Property):
    imageSize = 640
    zoom = 21

    def getPointLatLng(self, x, y):
        # print("getPointLatLng", lat, lng)
        parallelMultiplier = math.cos(self.lat * math.pi / 180)
        degreesPerPixelX = 360 / math.pow(2, self.zoom + 8)
        degreesPerPixelY = 360 / math.pow(2, self.zoom + 8) * parallelMultiplier
        pointLat = self.lat - degreesPerPixelY * (y - self.imageSize / 2)
        pointLng = self.lng + degreesPerPixelX * (x - self.imageSize / 2)
        return (pointLng, pointLat)

    def findPolygon(self):
        url = "http://maps.googleapis.com/maps/api/staticmap?center=%s,%s&zoom=%s&format=png32&size=%sx%s&maptype=roadmap&style=visibility:off&style=%s&key=%s" % (
            self.lat, self.lng, self.zoom, self.imageSize, self.imageSize,
            quote('feature:landscape.man_made|element:geometry.stroke|visibility:on|color:0xffffff|weight:1'),
            apiKey)

        resp = requests.get(url, stream=True).raw
        im = numpy.asarray(bytearray(resp.read()), dtype="uint8")
        im = cv2.imdecode(im, cv2.IMREAD_COLOR)
        imgray = cv2.cvtColor(im, cv2.COLOR_RGB2GRAY)
        ret, thresh = cv2.threshold(imgray, 127, 255, 0)
        contours, _ = cv2.findContours(thresh, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

        minDistance = sys.maxsize
        contour_idx = -1

        for idx, contour in enumerate(contours):
            distance = cv2.pointPolygonTest(contour, (self.imageSize / 2, self.imageSize / 2), True)
            if distance >= 0.0 and distance < minDistance:
                minDistance = distance
                contour_idx = idx

        if contour_idx > -1:
            points = cv2.approxPolyDP(contours[contour_idx], 0.01 * cv2.arcLength(contours[contour_idx], True), True)
            coordinates = []
            for point in points:
                coordinates.append(self.getPointLatLng(point[0][0], point[0][1]))
            coordinates.append(coordinates[0])
            return GIS.reprojectToOSGB36(Polygon(coordinates))
        else:
            return None
