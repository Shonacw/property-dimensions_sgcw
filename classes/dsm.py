from rasterstats import zonal_stats


class DSM:
    raster = r"data/DTM-DSM.tif"

    @staticmethod
    def getHeight(box):
        stats = zonal_stats(box, DSM.raster)
        if len(stats) > 0:
            return stats[0].get("max")
        else:
            return None
