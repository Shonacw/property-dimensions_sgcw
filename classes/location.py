from .osm import OSM, OSMProperty
from .google import Google, GoogleProperty
from .plot import Plot
from .garden import Garden


class Location:

    def __init__(self, lat, lng):
        self.lat = lat
        self.lng = lng
        self.road = OSM.getNearestRoad(lat, lng)
        if self.road is None:
            print("couldn't snap to nearest road using osrm")
            self.road = Google.getNearestRoad(lat, lng)
            if self.road is None:
                print("couldn't snap to nearest road using google")

    def getOSMProperty(self):
        return OSMProperty(self.lat, self.lng, self.road)

    def getGoogleProperty(self):
        return GoogleProperty(self.lat, self.lng, self.road)

    def getPlot(self):
        return Plot(self.lat, self.lng, self.road)

    def getGarden(self, property, plot):
        return Garden(self.lat, self.lng, self.road, property, plot)
