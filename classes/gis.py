import pyproj
import cmath
from shapely.geometry import LineString
from shapely.ops import transform


class GIS:
    wgs84 = pyproj.CRS("EPSG:4326")
    osgb36 = pyproj.CRS("EPSG:27700")
    project = pyproj.Transformer.from_crs(wgs84, osgb36, always_xy=True).transform
    project_back = pyproj.Transformer.from_crs(osgb36, wgs84, always_xy=True).transform

    @staticmethod
    def reproject(geom):
        return transform(GIS.project, geom)

    @staticmethod
    def reproject_back(geom):
        return transform(GIS.project_back, geom)

    @staticmethod
    def getBoundingBox(geom):
        return geom.minimum_rotated_rectangle

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
