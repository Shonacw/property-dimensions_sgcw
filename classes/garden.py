from shapely.geometry import LineString
from shapely.ops import transform, linemerge, unary_union, polygonize

from .gis import GIS
from .geometry import Geometry


class Garden(Geometry):

    def __init__(self, lat, lng, road, property, plot):
        self.property = property
        self.plot = plot
        super().__init__(lat, lng, road)

    @staticmethod
    def pairs(lst):
        for i in range(1, len(lst)):
            yield lst[i - 1], lst[i]

    def getFurthestWall(self):
        maxDistance = 0
        for pair in self.pairs(list(self.property.exterior.coords)):
            wall = LineString([pair[0], pair[1]])
            distance = self.road.distance(wall)
            if distance > maxDistance:
                maxDistance = distance
                furthestWall = wall

        return GIS.extendLine(furthestWall.coords, 10)

    def findPolygon(self):
        wall = self.getFurthestWall()
        merged = linemerge([self.plot.boundary, wall])
        borders = unary_union(merged)
        polygons = polygonize(borders)

        maxDistance = 0
        for p in polygons:
            d = self.road.distance(p)
            if d > maxDistance:
                maxDistance = d
                poly = p

        return poly
