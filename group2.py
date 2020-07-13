import re
import os
import pandas as pd
import requests
import pdb
import fiona
import glob
from shapely.geometry import shape, mapping, Point, Polygon, MultiPolygon
from zipfile import ZipFile

origin_dir = '/Users/gennadiigorbun/Documents/Lend_Direct_Local/2020/cmp/'
data_dir = '/Users/gennadiigorbun/Documents/Lend_Direct_Local/2020/project_data/'
inspire_dir = './inspire/'



def get_next_mp_sector(meta_df, target='beds_%'):
    target_arr = ['beds_%', 'area_%', 'age_%', 'sale_%', 'overlap1_%', 'overlap2_%']
    if target not in target_arr:
        raise Exception(f'Invalid Target: {target}. Choose one of {target_arr}')

    i = 0
    meta_df.sort_values(target, inplace=True, ascending=False)

    while i < len(meta_df):
        sector = meta_df.iloc[i].sector
        yield sector
        i += 1

def load_sector(sector):
    outer_code = re.split('\d', sector)[0].upper()
    os.chdir(f'{data_dir}/{outer_code}/')
    try:
        sec_df = pd.read_hdf(f'data_{sector}.h5')
    except(OSError, FileNotFoundError):
        raise Exception(f'Datafile for sector {sector} not found')
    return sec_df


def find_tile(lat, long):
    path = '/Users/gennadiigorbun/Documents/Lend_Direct_Local/2020/cmp/tiles_meta/tiles.shp'
    point = Point(long, lat)
    tile_dict = {'00' : 'sw', '05' : 'nw', '50' : 'se', '55' : 'ne'}
    sink_tilename = 'unknown'
    with fiona.open(path) as collection:
        for record in collection:
            #print(shape(record['geometry']))
            if point.within(shape(record['geometry'])):
                source_tilename = record['properties']['tilename']
                src_cd = re.findall(r'\d+', source_tilename)[0]
                reg = tile_dict[src_cd[1] + src_cd[3]]
                tile_num = src_cd[0] + src_cd[2]
                sink_tilename = re.split('\d+', source_tilename)[0] + tile_num + reg
                return sink_tilename
    return sink_tilename

def find_inspire(admin_district):
    search_res = glob.glob(inspire_dir + admin_district + '/' + '*.gml')
    if len(search_res) > 0:
        return search_res[0]
    else:
        return 'unknown'


def download_dstm(tile, key='dtm'):
    keys = ['dtm', 'dsm']
    url_temp = "https://environment.data.gov.uk/UserDownloads/interactive/997366256b5e4586bad6056d6ca1b57139064/NLP/National-LIDAR-Programme-%s-2018-%s.zip"
    if key.lower() not in keys:
        raise Exception(f'Invalid key {key}')
    key = key.upper()
    # Formatting the tile name as required:
    tile_parts = re.split(r'(\d)', tile)
    tile_parts[0] = tile_parts[0].upper(); tile_parts[-1] = tile_parts[-1].lower()
    tile = ''.join(tile_parts)
    try:
        url = url_temp % (key, tile)
        r = requests.get(url, allow_redirects=True)
        print(f'Downloading {key} tile {tile}...')
        fname = f'{key}_{tile}.zip'
        open(fname, 'wb').write(r.content)
        print('Done')
        return fname
    except:
        print('Whoops..')


def get_authority(postcode):
    url = f'http://api.postcodes.io/postcodes/{postcode}'
    r = requests.get(url)
    if r.ok:
        res_json = r.json()
        admin_district = r.json()['result']['admin_district']
        if admin_district == 'Westminster':
            admin_district = 'City of Westminster'
        #admin_district = '_'.join([word.capitalize() if word != 'and' else 'and' for word in admin_district.split(' ')])

        admin_district = admin_district.replace(' ', '_')
        return admin_district
    else:
        print(f'Postocdes.io errored with {r.status_code}')
        return None


def download_inspire(admin_district):
    url = "https://use-land-property-data.service.gov.uk/datasets/inspire/download/%s"
    print(f'Downloading INSPIRE data for {admin_district}')
    fname = f'{admin_district}.zip'
    try:
        r = requests.get(url % fname, allow_redirects=True)
        open(fname, 'wb').write(r.content)
        print('Done')
    except:
        print(f'Unable to download INSPIRE for {admin_district}')
        return None
    return fname

def unpack_inspire(fname):
    with ZipFile(fname, 'r')  as zipObj:
        zipObj.extractall(inspire_dir + fname[:-4] + '/')
    os.remove(fname)
    return fname[:-4]
