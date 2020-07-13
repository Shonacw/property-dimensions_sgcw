#!/bin/bash
data_dir="/Users/gennadiigorbun/Documents/Lend_Direct_Local/2020/cmp/tiles/"
fname="DTM-DSM-$1.tif"

function find_recent()
{
  dtm_f=$(ls -t ./*DTM*.zip | head -n 1)
  dsm_f=$(ls -t ./*DSM*.zip | head -n 1)
  echo "The following most recent DTM/DSM were found:"
  echo $dtm_f
  echo $dsm_f
  echo
}

function unzip_recent()
{
  echo 'Unzipping most recent DTM/DSM...'
  yes | unzip $dtm_f -d $data_dir
  yes | unzip $dsm_f -d $data_dir
  echo "Removing archives..."
  echo $dtm_f
  echo $dsm_f
  rm $dtm_f
  rm $dsm_f
}

function subtract_dtm_dsm()
{
  cd $data_dir
  new_dir=$(ls -t | head -n 1)
  cd $new_dir

  dtm_tif=$(ls -t *DTM*.tif | head -n 1)
  dsm_tif=$(ls -t *DSM*.tif | head -n 1)
  echo "Subtracting DTM from DSM..."
  gdal_calc.py -A $dsm_tif -B $dtm_tif --outfile $data_dir$fname --calc='A-B'
  echo "Done"
  echo "Removing pure data files..."
  cd ..
  rm -r $new_dir
  echo "Done"
}

find_recent && unzip_recent && subtract_dtm_dsm
