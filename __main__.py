import pandas as pd
import numpy as np
import argparse
import os, sys
import glob
import re
from subprocess import call
from group import get_next_mp_sector, load_sector, download_dstm, find_tile, download_inspire, get_authority, \
    find_inspire, unpack_inspire, get_authority_url, get_data   ####added import of _url and get data
# from dimensions import OSM, Google, Property, RearGarden, Plot, GIS, DSM
# from dimensions import get_dimensions, get_dimensions_lite
from classes.location import Location
#from dimensions import DSM, Plot
from classes.dsm import DSM
from classes.plot import Plot
import time

import requests

import pdb
#origin_dir = '/Users/gennadiigorbun/Documents/Lend_Direct_Local/2020/cmp/'
#data_dir = '/Users/gennadiigorbun/Documents/Lend_Direct_Local/2020/project_data/'
#ref_dir = '/Users/gennadiigorbun/Documents/Lend_Direct_Local/2020/ref/'

#origin_dir = '/Users/ShonaCW/PycharmProjects/property-dimensions/'
#data_dir = '/Users/ShonaCW/Desktop/project_data/'
#ref_dir = '/Users/ShonaCW/Desktop/project_data/ref_data/'

origin_dir = '/Users/ShonaCW/Desktop/Lend_Direct_Local/property-dimensions/'
data_dir ='/Users/ShonaCW/Desktop/Lend_Direct_Local/project_data/'
ref_dir ='/Users/ShonaCW/Desktop/Lend_Direct_Local/ref_data/'

outer_codes = ['BR', 'CR', 'DA', 'E', 'EC', 'EN', 'HA', 'IG', 'KT', 'N',
               'NW', 'RM', 'SE', 'SL', 'SM', 'ST', 'SW', 'TW', 'UB', 'W',
               'WC', 'WD']


##to replace get_dimensions (return organised dictionary of info rather than simply printing)
def run(lat, lng):
    """
    Params: lat long coordinates
    Returns: three lists and a string
    Notes: Currently using the -very- wrong method of sorting the width/ depth of a property as max/min. This will
    be removed or updated, only using it atm so we can get some reasonable stats for the particular street being tested.
    """
    status = 'Worked'
    loc = Location(lat, lng)

    plot = loc.getPlot()
    plotPolygon = plot.getPolygon()
    if plotPolygon is None:
        status = 'Plot failed'
    if plotPolygon is not None:
        # plotWidth, plotDepth, _ = plot.getDimensions()
        *widthdepth, _ = plot.getDimensions()
        plotDepth = max(widthdepth)
        plotWidth = min(widthdepth)
        plotArea = plot.getArea()
        plot_data = [plotWidth, plotDepth, plotArea]

    prop = loc.getOSMProperty()
    # propWidth, propDepth, _ = prop.getDimensions()
    *widthdepth, _ = prop.getDimensions()
    propDepth = max(widthdepth)
    propWidth = min(widthdepth)
    propArea = prop.getArea()
    propHeight = prop.getHeight()

    if plotPolygon is not None:
        land_area = plotArea - propArea
        garden = loc.getGarden(prop.getPolygon(), plot.getPolygon())
        # gardenWidth, gardenDepth, _ = garden.getDimensions()
        *widthdepth, _ = garden.getDimensions()
        gardenDepth = max(widthdepth)
        gardenWidth = min(widthdepth)
        gardenArea = garden.getArea()
        osm_data = [propWidth, propDepth, propHeight, propArea, land_area, gardenWidth, gardenDepth, gardenArea]

    prop = loc.getGoogleProperty()
    propWidth, propDepth, _ = prop.getDimensions(goog=True)
    if _ is not None:
        status = 'Linestring'

    propArea = prop.getArea()
    propHeight = prop.getHeight()

    if plotPolygon is not None:
        land_area = plotArea - propArea
        garden = loc.getGarden(prop.getPolygon(), plot.getPolygon())
        # gardenWidth, gardenDepth, _ = garden.getDimensions()
        *widthdepth, _ = garden.getDimensions()
        gardenDepth = max(widthdepth)
        gardenWidth = min(widthdepth)
        gardenArea = garden.getArea()
        goog_data = [propWidth, propDepth, propHeight, propArea, land_area, gardenWidth, gardenDepth, gardenArea]

    return plot_data, osm_data, goog_data, status
##


parser = argparse.ArgumentParser()
parser.add_argument('-so', '--single_outer', dest='so', type=str, default=False)
parser.add_argument('-meta', dest='mt', action='store_true', default=True)
args = parser.parse_args()

pd.set_option('display.max_rows', 20)
pd.set_option('display.max_columns', 20)
pd.set_option('display.width', 1000)

if __name__ == "__main__":
    if args.so:
        outer_code = args.so.upper()
        os.chdir(f'{data_dir}/{outer_code}/')
        print(glob.glob('*.h5'))
        df = pd.concat((pd.read_hdf(f, key='sector_data') for f in glob.glob('*.h5'))) #added key here
        df = df.reset_index(drop=True)

        os.chdir(f'{ref_dir}/{outer_code}/')
        print(glob.glob('*.h5'))
        ref_df = pd.concat((pd.read_hdf(f) for f in glob.glob('*.h5')))
        ref_df = ref_df.reset_index(drop=True)
        os.chdir(origin_dir)
        #pdb.set_trace()
        for key, group in ref_df.groupby(['street']):
            print('key', key)                                       #testing
            #pdb.set_trace()
            # dict to fill with dimension data and stats for eachstreet
            data_dict = {'status': [], 'plot_width': [], 'plot_depth': [], 'plot_area': [], 'width_osm': [],
                         'depth_osm': [],
                         'height_osm': [], 'area_osm': [], 'land_area_osm': [], 'rear_garden_width_osm': [],
                         'rear_garden_depth_osm': [], 'rear_garden_area_osm': [], 'width_goog': [], 'depth_goog': [],
                         'height_goog': [], 'area_goog': [], 'land_area_goog': [], 'rear_garden_width_goog': [],
                         'rear_garden_depth_goog': [], 'rear_garden_area_goog': []}

            # getting the actual data for the properties on the street
            data_group = df.loc[df['main_reference'].isin(group['main_reference'])]
            data_group.dropna(axis=0, subset=['t_lat', 't_long'], inplace=True)
            # now only the ones with coords are available
            for property in data_group.itertuples():
                #pdb.set_trace()
                lat = getattr(property, 't_lat')
                long = getattr(property, 't_long')
                print('lat-----', lat)                              #testing
                postcode = getattr(property, 'postcode')
                #### DSM/DTM
                try:
                    tilename = find_tile(lat, long)
                    #pdb.set_trace()
                    if tilename == 'unknown':
                        print('Could not find DSM tile, skipping...')
                        continue
                except:
                    print('Could not find DSM tile, skipping...')
                    continue

                # search for available DSM tiles
                available_tiles = glob.glob(f'./tiles/*{tilename}*.tif')
                print('available_tiles', available_tiles)
                #pdb.set_trace()
                if len(available_tiles) == 1:
                    print(f'Located the corresponding tile {tilename}')
                    dsm_file = available_tiles[0]
                elif len(available_tiles) > 1:
                    print(f'Unable to resolve instances of {tilename}, skipping...')
                    continue
                else:
                    print(f'Unable to locate {tilename}, downloading...')
                    try:
                        download_dstm(tilename, key='dsm')
                        download_dstm(tilename, key='dtm')
                    except:
                        print(f'Unable to download {tilename}, skipping...')
                        continue
                    try:
                        os.system('chmod u+rx unpack_dsm.sh')
                        rc = call([f"./unpack_dsm.sh", str(tilename)])
                    except:
                        raise Exception('Unable to unpack')

                print('----entering INSPIRE-----')                          #testing
                #pdb.set_trace()
                ## INSPIRE
                admin_district = get_authority_url(postcode)
                print('==ADMIN DISTRICT==', admin_district)                 #testing
                #pdb.set_trace()
                inspire_gml_path = find_inspire(admin_district)
                #pdb.set_trace()
                if inspire_gml_path == 'unknown':
                    print('Unable to locate local INSPIRE polygons, downloading...')
                    try:
                        inspire_zip_path = download_inspire(admin_district)  # fname includes .zip at this point
                    except:
                        raise Exception(f'Could not download INSPIRE polygons data for {postcode}')

                    try:
                        #pdb.set_trace()
                        print(inspire_zip_path)
                        inspire_dir_name = unpack_inspire(inspire_zip_path)
                        inspire_gml_path = glob.glob(origin_dir + 'inspire/' + inspire_dir_name + '/*.gml')[0]
                    except:
                        raise Exception(f'Could not unpack INSPIRE polygons data for {postcode}')

                print('----entering CALCULATIONS/SAVING-----')          #testing
                #pdb.set_trace()

                ##CALCULATE AND STORE DIMENSIONAL INFO
                dsm_path, inspire_path = get_data(lat, long)
                #pdb.set_trace()
                DSM.set_raster(dsm_path)
                Plot.set_inspire(inspire_path)

                plot_data, osm_data, goog_data, stat = run(lat, long) # Collect

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

                print("===========DONE ONE HOUSE============")              #testing
                print('status', data_dict['status'])
                print('width osm:', data_dict['width_osm'])
                print('width google', data_dict['width_goog'])

                #time.sleep(4) ## Required to avoid Overpass 'MultipleRequests' error

            ##SORT WIDTH AND DEPTH DATA
            affected_keys = ['plot_width', 'plot_depth', 'width_osm', 'depth_osm', 'rear_garden_width_osm',
                             'rear_garden_depth_osm', 'width_goog', 'depth_goog', 'rear_garden_width_goog',
                             'rear_garden_depth_goog']
            for i in range(0, len(affected_keys), 2):
                # First check whether changes are required..
                widths = [x for x in data_dict[affected_keys[i] if x is not None]
                median = np.median(widths)
                std = np.std(widths)
                if std < 0.25 * median:
                    continue
                else:
                    mean = np.mean(widths)
                    to_correct = min([[j for j in widths if j > mean], [j for j in widths if j < mean]], key=len)
                    indices = [i for i, e in enumerate(data_dict[affected_keys[i]]) if e in to_correct]
                    for j in indices:
                        a = data_dict[affected_keys[i]][j]
                        data_dict[affected_keys[i]][j] = data_dict[affected_keys[i + 1]][j]
                        data_dict[affected_keys[i + 1]][j] = a

            ## ADDING STATS TO DICT
            # relative standard deviation
            for name, my_list in data_dict.items():
                if name == 'status':
                    continue
                my_list = [i for i in my_list if i is not None]
                ## Note: ignoring 'None's that arise from Linestring errors, and the '0's which arise from measurement errors
                data_dict[f'rel_std_{name}'] = round(np.std(my_list) / np.mean(my_list), 4)

            # percentage of instances Plot data was obtained
            data_dict['perc_plot'] = round(int(len([x for x in plot_width if x is not None])) / int(len(plot_width)), 4) * 100
            # percentage of instances OSM data was obtained
            data_dict['perc_osm'] = round(int(len([x for x in width_osm if x is not None])) / int(len(width_osm)), 4) * 100
            # percentage of instances Google data was obtained
            data_dict['perc_goog'] = round(int(len([x for x in width_goog if x is not None])) / int(len(width_goog)), 4) * 100

            # percentage of Linestring error instances
            data_dict['perc_Linestring'] = round(int(len([x for x in status if x == 'Linestring'])) / int(len(status)), 4) * 100
            # percentage of None error instances
            data_dict['perc_None'] = round(int(len([x for x in status if x == 'None'])) / int(len(status)), 4) * 100
            #percentage of Plot-Failed error instances
            data_dict['perc_PlotFail'] = round(int(len([x for x in status if x == 'Plot failed'])) / int(len(status)), 4) * 100


            ##SAVING DICT TO CSV (?) FILE
            street_name = key.replace(" ", "_")
            df = pd.DataFrame.from_dict(data_dict, orient='index').transpose()
            df.to_csv(f'{data_dir}/streets_data/dim_{street_name}.csv')

            print(data_dict) # (testing)

"""
if args.mt:
    os.chdir(f'{data_dir}/')
    try:
        meta_df = pd.read_hdf('internship_statistics.h5')
    except(OSError, FileNotFoundError):
        os.chdir('../cmp/')
        raise Exception('Meta stats file not found')

    os.chdir('../cmp/')
"""
