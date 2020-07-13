from osgeo import ogr
import shapely.wkt
from shapely.geometry import Point

from .gis import GIS
from .geometry import Geometry


class Plot(Geometry):
    file = r"data/Barnet.gml"
    #file = "/Users/ShonaCW/Pycharmprojects/new/Land_Registry_Cadastral_Parcels.gml"

    @classmethod
    def set_inspire(cls, fname):
        cls.file = fname

    def __init__(self, lat, lng, road):
        super().__init__(lat, lng, road)

    def findPolygon(self):
        source = ogr.Open(self.file)
        layer = source.GetLayer()
        point = GIS.reprojectToOSGB36(Point(self.lng, self.lat))

        while True:
            feature = layer.GetNextFeature()
            if feature is None:
                break
            geom = feature.GetGeometryRef()
            wkt = geom.ExportToWkt()
            poly = shapely.wkt.loads(wkt)
            within = point.within(poly)
            if within:
                return poly

        print("plot not found")
        return None
