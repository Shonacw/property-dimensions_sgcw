from abc import abstractmethod
from shapely.geometry import Point

from .gis import GIS


class Geometry:

    def __init__(self, lat, lng, road):
        self.lat = lat
        self.lng = lng
        self.road = road
        self.polygon = self.findPolygon()

    @abstractmethod
    def findPolygon(self):
        pass

    def getPolygon(self):
        # if self.polygon is None:
        # print("no building found")
        # return None, None, None
        return self.polygon

    def getDimensions(self):
        if self.polygon is not None:
            box = GIS.getBoundingBox(self.polygon)
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

            return width, depth
        else:
            return None, None

    def getArea(self):
        return self.polygon.area
