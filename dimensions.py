import sys

from classes.location import Location

if len(sys.argv) != 3:
    print("usage: dimensions.py lat lng")
    exit(1)

try:
    lat = float(sys.argv[1])
    lng = float(sys.argv[2])

    loc = Location(lat, lng)

    plot = loc.getPlot()
    plotPolygon = plot.getPolygon()
    if plotPolygon is not None:
        plotWidth, plotDepth = plot.getDimensions()
        plotArea = plot.getArea()
        print("plot width", plotWidth)
        print("plot depth", plotDepth)
        print("plot area", plotArea)
        print("")

    prop = loc.getOSMProperty()
    propWidth, propDepth = prop.getDimensions()
    propArea = prop.getArea()
    propHeight = prop.getHeight()
    print("OSM")
    print("property width", propWidth)
    print("property depth", propDepth)
    if propHeight is not None:
        print("property height", propHeight)
    print("property area", propArea)

    if plotPolygon is not None:
        print("land area", plotArea - propArea)
        garden = loc.getGarden(prop.getPolygon(), plot.getPolygon())
        gardenWidth, gardenDepth = garden.getDimensions()
        gardenArea = garden.getArea()
        print("rear garden width", gardenWidth)
        print("rear garden depth", gardenDepth)
        print("rear garden area", gardenArea)
        print("")

    prop = loc.getGoogleProperty()
    propWidth, propDepth = prop.getDimensions()
    propArea = prop.getArea()
    propHeight = prop.getHeight()
    print("Google")
    print("property width", propWidth)
    print("property depth", propDepth)
    if propHeight is not None:
        print("property height", propHeight)
    print("property area", propArea)

    if plotPolygon is not None:
        print("land area", plotArea - propArea)
        garden = loc.getGarden(prop.getPolygon(), plot.getPolygon())
        gardenWidth, gardenDepth = garden.getDimensions()
        gardenArea = garden.getArea()
        print("rear garden width", gardenWidth)
        print("rear garden depth", gardenDepth)
        print("rear garden area", gardenArea)

except ValueError:
    print("params must be numbers")
    exit()

except:
    print("something went wrong")
    exit()
