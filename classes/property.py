from .geometry import Geometry
from .dsm import DSM


class Property(Geometry):
    def __init__(self, lat, lng, road):
        super().__init__(lat, lng, road)

    def getHeight(self):
        return DSM.getHeight(self.polygon)
