import pandas as pd
import numpy as np
import time

from dimensions import run

#from group import download_dstm, find_tile
#51.576477 -0.099432 is giving 0.2 as property width from google and is highlighting all surrounding polygon
#51.576485 -0.099359 is giving linestring error and is only highlighting the wall between the two properties


def Testing_Anatoly_Road(Road_Name, sector_df, print_info=False):
    """
    Params: the name of road as a string, i.e. "Lothair Road North", the LD dataframe of the relevant sector
    Optional Params: set print_info=True to display info collected

    Returns: A dictionary of collected info. See 'data_dict' below for dict items.

    Notes: Currently specifying the sector dataframe within this function, for the example. Will be removed. Also
            currently only looping through 5 houses on the street bc its slow af.
    """
    idxs = [idx for idx, c in sector_df.iterrows() if Road_Name in c["address"]]
    lats = sector_df.iloc[idxs]['t_lat'][16:20]                                                  #eventually remove this
    longs = sector_df.iloc[idxs]['t_long'][16:20]

    data_dict = {'status': [], 'plot_width': [], 'plot_depth': [], 'plot_area': [], 'width_osm': [], 'depth_osm': [],
                 'height_osm': [], 'area_osm': [], 'land_area_osm': [], 'rear_garden_width_osm': [],
                 'rear_garden_depth_osm': [], 'rear_garden_area_osm': [], 'width_goog': [], 'depth_goog': [],
                 'height_goog': [], 'area_goog': [], 'land_area_goog': [], 'rear_garden_width_goog': [],
                 'rear_garden_depth_goog': [], 'rear_garden_area_goog': []}

    for lat, lng in zip(lats, longs):
        print(lat, lng)
        if np.isnan(lat):
            continue
        plot_data, osm_data, goog_data, stat = run(lat, lng)

        data_dict['status'].append(stat)

        data_dict['plot_width'].append(plot_data[0])
        data_dict['plot_depth'].append(plot_data[1])
        data_dict['plot_area'].append(plot_data[2])

        data_dict['width_osm'].append(osm_data[0])
        data_dict['depth_osm'].append(osm_data[1])
        data_dict['height_osm'].append(osm_data[2])
        data_dict['area_osm'].append(osm_data[3])
        data_dict['land_area_osm'].append(osm_data[4])
        data_dict['rear_garden_width_osm'].append(osm_data[5])
        data_dict['rear_garden_depth_osm'].append(osm_data[6])
        data_dict['rear_garden_area_osm'].append(osm_data[7])

        data_dict['width_goog'].append(goog_data[0])
        data_dict['depth_goog'].append(goog_data[1])
        data_dict['height_goog'].append(goog_data[2])
        data_dict['area_goog'].append(goog_data[3])
        data_dict['land_area_goog'].append(goog_data[4])
        data_dict['rear_garden_width_goog'].append(goog_data[5])
        data_dict['rear_garden_depth_goog'].append(goog_data[6])
        data_dict['rear_garden_area_goog'].append(goog_data[7])

        time.sleep(3) ## Required to avoid Overpass 'MultipleRequests' error

    if print_info == True:
        print("")
        print(data_dict['status'])
        print("")
        for name, my_list in data_dict.items():
            print(name)
            print(my_list)
            if name == 'status':
                continue

            my_list = [i for i in my_list if i is not None]
            ## Note: ignoring 'None's that arise from Linestring errors, and the '0's which arise from measurement errors
            print(round(np.std(my_list)/np.mean(my_list), 4))
        return

    else:
        return data_dict


sector_df = pd.read_hdf('/Users/ShonaCW/Desktop/project_data/N/data_N4_1.h5', key='sector_data')
Testing_Anatoly_Road("Lothair Road North", sector_df, print_info=True)
