import re
import os
import pandas as pd
import requests
import pdb
import fiona
import glob
from shapely.geometry import shape, mapping, Point, Polygon, MultiPolygon
from zipfile import ZipFile
from pathlib import Path
#from dimensions import DSM, Plot
from osgeo import ogr
from subprocess import call
import shutil

from classes.dsm import DSM
from classes.plot import Plot

origin_dir = Path(os.path.abspath(__file__)).parent # be careful, this is only cmp if group.py is in cmp
#origin_dir = Path('/Users/ShonaCW/Desktop/Lend_Direct_Local/property-dimensions/')
data_dir = Path('/Users/ShonaCW/Desktop/Lend_Direct_Local/project_data/')

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
    oc_dir = data_dir / f"{outer_code}"
    os.chdir(oc_dir)
    try:
        sec_df = pd.read_hdf(f'data_{sector}.h5')
    except(OSError, FileNotFoundError):
        raise Exception(f'Datafile for sector {sector} not found')
    return sec_df


def find_tile(lat, long):
    path = origin_dir / 'tiles_meta' / 'tiles.shp'
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
    try:
        #pdb.set_trace()
        admin_path = origin_dir / 'inspire' / admin_district
    except:
        print('what the shit')
    if admin_path.exists():

        search_res = [i for i in admin_path.glob('*.gml')]
        if len(search_res) > 0:
            return search_res[0]
        else:
            return 'unknown'
    else:
        return 'unknown'


def download_dstm(tile, key='dtm'):
    keys = ['dtm', 'dsm']
    url_temp = "https://environment.data.gov.uk/UserDownloads/interactive/ad5b89f64b7147e18c6b5945d9ed52b149080/NLP/National-LIDAR-Programme-%s-2018-%s.zip"
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


def get_authority_url(postcode):
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


def get_authority(lat, long):
    inspire_meta_path = origin_dir / "inspire_meta" / "INSPIRE_AdministrativeUnit.shp"
    #source = ogr.Open(str(inspire_meta_path))

    point = Point(long, lat)
    authority = 'unknown'
    with fiona.open(str(inspire_meta_path)) as source:
        for record in source:
            if point.within(shape(record['geometry'])):
                if record['properties']['gml_id'] != 'osgb7000000000041441':
                    authority = record['properties']['text']
        if authority == 'Westminster':
            authority = 'City_of_Westminster'
        authority = authority.replace(' ', '_')
        authority = authority.replace('And', 'and')
    return authority


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
        zip_path = origin_dir / "inspire" / fname[:-4]
        zipObj.extractall(zip_path)
    os.remove(fname)
    return fname[:-4]


def unpack_dstm(tilename):
    print('tilename', tilename)
    tiles_dir = origin_dir / "tiles"
    fname = f'DTM-DSM-{tilename}'
    dtm_zip = origin_dir.glob(f'DTM_{tilename}.zip')
    dtm_zip = list(dtm_zip)[0]
    print('+++DTM ZIP', dtm_zip)
    with ZipFile(dtm_zip, 'r') as zipObj:
        zip_path = origin_dir / "tiles"
        zipObj.extractall(zip_path)
    os.remove(dtm_zip)

    dsm_zip = origin_dir.glob(f'*DSM*{tilename}.zip')
    dsm_zip = list(dsm_zip)[0]
    with ZipFile(dsm_zip, 'r') as zipObj:
        zip_path = origin_dir / "tiles"
        zipObj.extractall(zip_path)
    os.remove(dsm_zip)
    os.chdir(origin_dir / 'tiles')
    dirs = [d for d in os.listdir('.') if os.path.isdir(d)]
    zip_dir = max(dirs, key=os.path.getmtime)
    zip_dir = origin_dir / "tiles" / zip_dir
    os.chdir(origin_dir)
    dsm_res = zip_dir.glob(f"*DSM*.tif")
    dsm_tif = list(dsm_res)[0]
    dtm_res = zip_dir.glob(f"*DTM*.tif")
    dtm_tif = list(dtm_res)[0]
    out_tif = str(origin_dir / 'tiles' / f"DTM-DSM-{tilename}.tif")
    rc = call(["gdal_calc.py", "-A", str(dsm_tif), "-B", str(dtm_tif), "--outfile", str(out_tif), "--calc", "A-B"])
    try:
        shutil.rmtree(zip_dir)
    except OSError as e:
        print("Error: %s : %s" % (zip_dir, e.strerror))



def get_data(lat, long):
    print('LAT, LONG', lat, long)
    #### DSM/DTM
    try:
        tilename = find_tile(lat, long)
        if tilename == 'unknown':
            print('Could not find DSM tile, skipping...')
            return
    except:
        print('Could not find DSM tile, skipping...')
        return
    # search for available DSM tiles
    tiles_dir = origin_dir / "tiles"
    available_tiles = list(tiles_dir.glob(f'*{tilename}*.tif'))
    if len(available_tiles) == 1:
        print(f'Located the corresponding tile {tilename}')
        dsm_file = available_tiles[0]
    elif len(available_tiles) > 1:
        print(f'Unable to resolve instances of {tilename}, skipping...')
        return
    else:
        print(f'Unable to locate {tilename}, downloading...')
        try:
            dsm_zip = download_dstm(tilename, key='dsm')
            dtm_zip = download_dstm(tilename, key='dtm')
        except:
            print(f'Unable to download {tilename}, skipping...')
            return
        try:
            unpack_dstm(tilename)
        except:
            raise Exception('Unable to unpack')

    #### INSPIRE

    admin_district = get_authority(lat, long)
    print(admin_district)

    inspire_gml_path = find_inspire(admin_district)
    if inspire_gml_path == 'unknown':
        print('Unable to locate local INSPIRE polygons, downloading...')
        try:
            inspire_zip_path = download_inspire(admin_district) #fname includes .zip at this point
        except:
            raise Exception(f'Could not download INSPIRE polygons data for {postcode}')

        try:
            inspire_dir_name = unpack_inspire(inspire_zip_path)
            inspire_dir = origin_dir / 'inspire' / inspire_dir_name
            inspire_gml_path = list(inspire_dir.glob('*.gml'))[0]
        except:
            raise Exception(f'Could not unpack INSPIRE polygons data for {postcode}')
    else:
        print(f"Located INSPIRE data for {admin_district}...")


    dsm_tif_path = origin_dir / "tiles" / f"DTM-DSM-{tilename}.tif"
    return str(dsm_tif_path), str(inspire_gml_path)
