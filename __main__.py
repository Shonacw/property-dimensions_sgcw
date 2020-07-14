import pandas as pd
import numpy as np
import argparse
import os, sys
import glob
import re
from subprocess import call
from group import get_next_mp_sector, load_sector, download_dstm, find_tile, download_inspire, get_authority, find_inspire, unpack_inspire
#from dimensions import OSM, Google, Property, RearGarden, Plot, GIS, DSM
#from dimensions import get_dimensions, get_dimensions_lite
from classes.location import Location

import requests


import pdb


origin_dir = '/Users/gennadiigorbun/Documents/Lend_Direct_Local/2020/cmp/'
data_dir = '/Users/gennadiigorbun/Documents/Lend_Direct_Local/2020/project_data/'
ref_dir = '/Users/gennadiigorbun/Documents/Lend_Direct_Local/2020/ref/'


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
        #plotWidth, plotDepth, _ = plot.getDimensions()
        *widthdepth, _ = plot.getDimensions()
        plotDepth = max(widthdepth)
        plotWidth = min(widthdepth)
        plotArea = plot.getArea()
        plot_data = [plotWidth, plotDepth, plotArea]

    prop = loc.getOSMProperty()
    #propWidth, propDepth, _ = prop.getDimensions()
    *widthdepth, _ = prop.getDimensions()
    propDepth = max(widthdepth)
    propWidth = min(widthdepth)
    propArea = prop.getArea()
    propHeight = prop.getHeight()

    if plotPolygon is not None:
        land_area= plotArea - propArea
        garden = loc.getGarden(prop.getPolygon(), plot.getPolygon())
        #gardenWidth, gardenDepth, _ = garden.getDimensions()
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
        #gardenWidth, gardenDepth, _ = garden.getDimensions()
        *widthdepth, _ = garden.getDimensions()
        gardenDepth = max(widthdepth)
        gardenWidth = min(widthdepth)
        gardenArea = garden.getArea()
        goog_data = [propWidth, propDepth, propHeight, propArea, land_area, gardenWidth, gardenDepth, gardenArea]

    return plot_data, osm_data, goog_data, status




parser = argparse.ArgumentParser()
parser.add_argument('-so', '--single_outer', dest='so', type=str, default=False)
parser.add_argument('-meta', dest='mt', action='store_true', default=True)
args = parser.parse_args()

pd.set_option('display.max_rows', 20)
pd.set_option('display.max_columns', 15)
pd.set_option('display.width', 1000)

if __name__ == "__main__":
    if args.so:
        outer_code = args.so.upper()
        os.chdir(f'{data_dir}/{outer_code}/')
        print(glob.glob('*.h5'))
        df = pd.concat((pd.read_hdf(f) for f in glob.glob('*.h5')))
        df = df.reset_index(drop=True)

        os.chdir(f'{ref_dir}/{outer_code}/')
        print(glob.glob('*.h5'))
        ref_df = pd.concat((pd.read_hdf(f) for f in glob.glob('*.h5')))
        ref_df = ref_df.reset_index(drop=True)
        os.chdir(origin_dir)

        for key, group in ref_df.groupby(['street']):
           #dict to fill with dimension data for street
           data_dict = {'status': [], 'plot_width': [], 'plot_depth': [], 'plot_area': [], 'width_osm': [], 'depth_osm': [],
                 'height_osm': [], 'area_osm': [], 'land_area_osm': [], 'rear_garden_width_osm': [],
                 'rear_garden_depth_osm': [], 'rear_garden_area_osm': [], 'width_goog': [], 'depth_goog': [],
                 'height_goog': [], 'area_goog': [], 'land_area_goog': [], 'rear_garden_width_goog': [],
                 'rear_garden_depth_goog': [], 'rear_garden_area_goog': []}
          
            # getting the actual data for the properties on the street
            data_group = df.loc[df['main_reference'].isin(group['main_reference'])]
            data_group.dropna(axis=0, subset=['t_lat', 't_long'], inplace=True)
            # now only the ones with coords are available
            for property in data_group.itertuples():
                lat = getattr(property, 't_lat')
                long = getattr(property, 't_long')
                postcode = getattr(property, 'postcode')
                #### DSM/DTM
                try:
                    tilename = find_tile(lat, long)
                    if tilename == 'unknown':
                        print('Could not find DSM tile, skipping...')
                        continue
                except:
                    print('Could not find DSM tile, skipping...')
                    continue
                # search for available DSM tiles
                available_tiles = glob.glob(f'./tiles/*{tilename}*.tif')
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

                #### INSPIRE
                admin_district = get_authority(postcode)
                inspire_gml_path = find_inspire(admin_district)
                if inspire_gml_path == 'unknown':
                    print('Unable to locate local INSPIRE polygons, downloading...')
                    try:
                        inspire_zip_path = download_inspire(admin_district) #fname includes .zip at this point
                    except:
                        raise Exception(f'Could not download INSPIRE polygons data for {postcode}')

                    try:
                        pdb.set_trace()
                        inspire_dir_name = unpack_inspire(inspire_zip_path)
                        inspire_gml_path = glob.glob(origin_dir + 'inspire/' + inspire_dir_name +'/*.gml')[0]
                    except:
                        raise Exception(f'Could not unpack INSPIRE polygons data for {postcode}')


                #### Calculating dimensions and Storing
                DSM.set_raster(f'./tiles/DTM-DSM-{tilename}.tif')
                Plot.set_inspire(inspire_gml_path)
                print(getattr(property, 'address'))
                #get_dimensions(lat, long)
                plot_data, osm_data, goog_data, stat  = run(lat, long)
                
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
                
                #time.sleep(3) ## Required to avoid Overpass 'MultipleRequests' error
                
                #now want to save dict data to a file...
                df = pd.DataFrame.from_dict(data_dict ,orient='index').transpose()
                df.to_csv('file_name.csv')
                
                #data is now saved in dict, but we print here to check it worked
                for name, my_list in data_dict.items():
                  print(name)
                  print(my_list)
                  if name == 'status':
                      continue

                  my_list = [i for i in my_list if i is not None]
                  ## Note: ignoring 'None's that arise from Linestring errors, and the '0's which arise from measurement errors
                  print(round(np.std(my_list)/np.mean(my_list), 4))
                



    if args.mt:
        os.chdir(f'{data_dir}/')
        try:
            meta_df = pd.read_hdf('internship_statistics.h5')
        except(OSError, FileNotFoundError):
            os.chdir('../cmp/')
            raise Exception('Meta stats file not found')

        os.chdir('../cmp/')



    # b_gen = get_next_mp_sector(meta_df, target='beds_%')
    # sector = next(b_gen)
    # df_sec = load_sector(sector)
    # tile = 'tq27ne'
    # key = 'dsm'
    # download_dstm(tile, key)


    #tile = find_tile(-0.152607, 51.468325)
    #tile = find_tile(-0.219689, 51.487404)
    #print(tile)
