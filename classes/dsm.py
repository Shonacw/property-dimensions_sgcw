from rasterstats import zonal_stats, point_query
from shapely.geometry import Point
from .gis import GIS


class DSM:
    raster = r"data/DTM-DSM.tif"
    #raster = r"/Users/ShonaCW/PycharmProjects/new/DTM-DSM.tif"

    @classmethod
    def set_raster(cls, raster_file):
        cls.raster = raster_file

    @staticmethod
    def getHeight(box, lat, lng):
        point = GIS.reprojectToOSGB36(Point(lng, lat))
        value = point_query(point, DSM.raster)
        if value[0] is None:
            print("dsm not found")
            return None
        else:
            stats = zonal_stats(box, DSM.raster)
            if len(stats) > 0:
                return stats[0].get("max")
            else:
                return None
