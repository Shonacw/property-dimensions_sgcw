import sys

from classes.location import Location

if __name__ == "__main__":
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
            #plotWidth, plotDepth, _ = plot.getDimensions() #added
            *widthdepth, _ = garden.getDimensions()
            plotDepth = max(widthdepth)
            plotWidth = min(widthdepth)
            plotArea = plot.getArea()
            print("plot width", plotWidth)
            print("plot depth", plotDepth)
            print("plot area", plotArea)
            print("")

        print("OSM")
        prop = loc.getOSMProperty()
        #propWidth, propDepth, _ = prop.getDimensions()
        *widthdepth, _ = garden.getDimensions()
        propDepth = max(widthdepth)
        propWidth = min(widthdepth)
        propArea = prop.getArea()
        propHeight = prop.getHeight()
        print("property width", propWidth)
        print("property depth", propDepth)
        if propHeight is not None:
            print("property height", propHeight)
        print("property area", propArea)

        if plotPolygon is not None:
            print("land area", plotArea - propArea)
            garden = loc.getGarden(prop.getPolygon(), plot.getPolygon())
            #gardenWidth, gardenDepth, _ = garden.getDimensions()
            *widthdepth, _ = garden.getDimensions()
            gardenDepth = max(widthdepth)
            gardenWidth = min(widthdepth)
            gardenArea = garden.getArea()
            print("rear garden width", gardenWidth)
            print("rear garden depth", gardenDepth)
            print("rear garden area", gardenArea)
            print("")

        print("Google")
        prop = loc.getGoogleProperty()
        propWidth, propDepth, _ = prop.getDimensions(goog=True)
        if _ is not None:
            print("LineString Error")
        propArea = prop.getArea()
        propHeight = prop.getHeight()
        print("property width", propWidth)
        print("property depth", propDepth)
        if propHeight is not None:
            print("property height", propHeight)
        print("property area", propArea)

        if plotPolygon is not None:
            print("land area", plotArea - propArea)
            garden = loc.getGarden(prop.getPolygon(), plot.getPolygon())
            #gardenWidth, gardenDepth, _ = garden.getDimensions()
            *widthdepth, _ = garden.getDimensions()
            gardenDepth = max(widthdepth)
            gardenWidth = min(widthdepth)
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

def run(lat, lng):
    status = 'Worked'
    loc = Location(lat, lng)

    plot = loc.getPlot()
    plotPolygon = plot.getPolygon()
    if plotPolygon is not None:
        #plotWidth, plotDepth, _ = plot.getDimensions() ############################################
        *widthdepth, _ = plot.getDimensions()
        plotDepth = max(widthdepth)
        plotWidth = min(widthdepth)
        plotArea = plot.getArea()
        plot_data = [plotWidth, plotDepth, plotArea]

    prop = loc.getOSMProperty()
    #propWidth, propDepth, _ = prop.getDimensions()
    *widthdepth, _ = garden.getDimensions()
    propDepth = max(widthdepth)
    propWidth = min(widthdepth)
    propArea = prop.getArea()
    propHeight = prop.getHeight()

    if plotPolygon is not None:
        land_area= plotArea - propArea
        garden = loc.getGarden(prop.getPolygon(), plot.getPolygon())
        #gardenWidth, gardenDepth, _ = garden.getDimensions() ################(will need to change)#####
        *widthdepth, _ = garden.getDimensions()
        gardenDepth = max(widthdepth)
        gardenWidth = min(widthdepth)
        gardenArea = garden.getArea()
        osm_data = [propWidth, propDepth, propHeight, propArea, land_area, gardenWidth, gardenDepth, gardenArea]

    prop = loc.getGoogleProperty()
    #propWidth, propDepth, _ = prop.getDimensions(goog=True)
    *widthdepth, _ = garden.getDimensions(goog=True)
    propDepth = max(widthdepth)
    propWidth = min(widthdepth)
    if _ is not None:
        status = 'Linestring'

    propArea = prop.getArea()
    propHeight = prop.getHeight()

    if plotPolygon is not None:
        land_area = plotArea - propArea
        garden = loc.getGarden(prop.getPolygon(), plot.getPolygon())
        #gardenWidth, gardenDepth, _ = garden.getDimensions() #######################
        *widthdepth, _ = garden.getDimensions()
        gardenDepth = max(widthdepth)
        gardenWidth = min(widthdepth)
        gardenArea = garden.getArea()
        goog_data = [propWidth, propDepth, propHeight, propArea, land_area, gardenWidth, gardenDepth, gardenArea]

    return plot_data, osm_data, goog_data, status


#51.576248 -0.100351           111 lothair
#51.576374 -0.099855           125 Lothair
