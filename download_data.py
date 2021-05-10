#Example of how to download data using a python library.
#sentinelsat is the library to download the data]
#geopandas deal with the vector data
#shapely is used to deal with geometries of the shapefile
from sentinelsat import SentinelAPI, read_geojson, geojson_to_wkt
import sentinelsat
from datetime import date
from collections import OrderedDict
import geopandas as gpd
import os
from shapely.geometry import Polygon
import random

# The date range you will use to search images from. You can use strings or datetime.
d1 = "20200101"
d2 = "20200201"

# The file you will use to search image from. It could be any type of geometry,
# but the library only accept .geojson files. To be able to read shapefiles, we need to
# read with another library and convert the geometry to WKT.
file = ''
outpath = ''

# Maximum cloud percentage of the images.
cloud = 0.0

# This function will be used to create another polygon, from the bounding box of the shapefile
def get_bounds(gdf,index):
    minx, miny, maxx, maxy = gdf['geometry'][index].bounds
    # minx, miny, maxx, maxy = gdf['geometry'].bounds
    # minx = min(minx)
    # miny = min(miny)
    # maxx = max(maxx)
    # maxy = max(maxy)
    p = Polygon([[minx,maxy] , [maxx,maxy] , [maxx,miny] , [minx,miny]])
    return p.to_wkt()

# To be able to download the data, you should register yourself on copernicus website:
# https://scihub.copernicus.eu/dhus/#/self-registration
user = ''
password = ''
api = SentinelAPI(user, password)

# Reading the file and converting it to 
gdf = gpd.read_file(file)
gdf.to_crs(epsg=4326,inplace=True)

for i in gdf.index:
    footprint = get_bounds(gdf,i)
    query_kwargs = {'area':footprint,
                    'platformname': 'Sentinel-2',
                    'cloudcoverpercentage':(0.0,cloud),
                    'date': (d1, d2)}

    products = api.query(**query_kwargs)

    gdf2 = api.to_geodataframe(products)
    print(f'Images found: {len(gdf2)}')
    # Here you could create filters to remove some images

    # Downloading the data
    re = api.download_all(gdf2.index.to_list(),outpath)
