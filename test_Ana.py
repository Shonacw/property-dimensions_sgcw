from dimensions import run

#from group import download_dstm, find_tile
import pandas as pd
import numpy as np
import time

N4_1_df = pd.read_hdf('/Users/ShonaCW/Desktop/project_data/N/data_N4_1.h5', key='sector_data')
idxs = [idx for idx, c in N4_1_df.iterrows() if "Lothair" and "North" in c["address"]]

status = []

plot_width = []
plot_depth = []
plot_area = []

width_osm = []
depth_osm = []
height_osm = []
area_osm = []
land_area_osm = []
rear_garden_width_osm = []
rear_garden_depth_osm = []
rear_garden_area_osm = []

width_goog = []
depth_goog = []
height_goog = []
area_goog = []
land_area_goog = []
rear_garden_width_goog = []
rear_garden_depth_goog = []
rear_garden_area_goog = []

lats = N4_1_df.iloc[idxs]['t_lat'][0:20]
longs = N4_1_df.iloc[idxs]['t_long'][0:20]

#51.576477 -0.099432 is giving 0.2 as property width from google and is highlighting all surrounding polygon
#51.576485 -0.099359 is giving linestring error and is only highlighting the wall between the two properties

for lat, lng in zip(lats, longs):
    print(lat, lng)
    if np.isnan(lat):
        print("gotcha")
        continue
    plot_data, osm_data, goog_data, stat = run(lat, lng)

    status.append(stat)

    plot_width.append(plot_data[0])
    plot_depth.append(plot_data[1])
    plot_area.append(plot_data[2])

    width_osm.append(osm_data[0])
    depth_osm.append(osm_data[1])
    height_osm.append(osm_data[2])
    area_osm.append(osm_data[3])
    land_area_osm.append(osm_data[4])
    rear_garden_width_osm.append(osm_data[5])
    rear_garden_depth_osm.append(osm_data[6])
    rear_garden_area_osm.append(osm_data[7])

    width_goog.append(goog_data[0])
    depth_goog.append(goog_data[1])
    height_goog.append(goog_data[2])
    area_goog.append(goog_data[3])
    land_area_goog.append(goog_data[4])
    rear_garden_width_goog.append(goog_data[5])
    rear_garden_depth_goog.append(goog_data[6])
    rear_garden_area_goog.append(goog_data[7])
    time.sleep(3)

data_lists = {'plot_width': plot_width,'plot_depth': plot_depth, 'plot_area': plot_area, 'width_osm':width_osm,
              'depth_osm': depth_osm, 'height_osm': height_osm, 'area_osm': area_osm, 'land_area_osm': land_area_osm,
              'rear_garden_width_osm': rear_garden_width_osm, 'rear_garden_depth_osm': rear_garden_depth_osm,
              'rear_garden_area_osm': rear_garden_area_osm, 'width_goog': width_goog, 'depth_goog': depth_goog,
              'height_goog': height_goog, 'area_goog': area_goog, 'land_area_goog': land_area_goog,
              'rear_garden_width_goog': rear_garden_width_goog, 'rear_garden_depth_goog': rear_garden_depth_goog,
              'rear_garden_area_goog': rear_garden_area_goog}
print("")
print("")
print(status)
print("")

for name, list in data_lists.items():
    print(name)
    print(list)
    list = [i for i in list if i is not None] #and i !=0    #ignore the zeros which also arise from errors
    std = np.std(list)
    mean = np.mean(list)
    print(std/mean)
