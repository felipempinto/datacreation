from osgeo import gdal
import os
import pathlib
from tqdm import tqdm
import numpy as np
import rasterio
from shapely.geometry import Polygon
from rasterio.mask import mask
import geopandas as gpd

path_images = '/media/felipe/3dbf30eb-9bce-46d8-a833-ec990ba72625/Documentos/Empresa/Upwork/Harald/Project2/data/imgs'
shp_points = '/media/felipe/3dbf30eb-9bce-46d8-a833-ec990ba72625/Documentos/Empresa/Upwork/Harald/Project2/shps/southafrica.shp'
outpath = '/media/felipe/3dbf30eb-9bce-46d8-a833-ec990ba72625/Documentos/Empresa/Upwork/Harald/Project2/data/test'
size = 512

if not os.path.exists(outpath):
    os.mkdir(outpath)

def get_bounds(img):
    minx, xres, _, maxy, _, yres  = img.GetGeoTransform()
    maxx = minx + (img.RasterXSize * xres)
    miny = maxy + (img.RasterYSize * yres)
    return Polygon([[minx,maxy],[maxx,maxy],[maxx,miny],[minx,miny]])

def get_bounds_shp(geometry):
    minx,miny,maxx,maxy = geometry.bounds
    return Polygon([[minx,maxy],[maxx,maxy],[maxx,miny],[minx,miny]])

def create_new_geom(x,y,size,resolution):
    minx = x-(((size/2)*resolution)-(resolution/2))
    maxx = x+(((size/2)*resolution)-(resolution/2))
    miny = y-(((size/2)*resolution)-(resolution/2))
    maxy = y+(((size/2)*resolution)-(resolution/2))
    # return minx,miny,maxx,maxy
    return Polygon([[minx,maxy],[maxx,maxy],[maxx,miny],[minx,miny]])

def clip(img,wkt,output):
    with rasterio.open(img) as src:
        out_image, out_transform = mask(src, [wkt], crop=True)
        out = out_image[out_image!=0]
        if len(out)==0:
            return
        out_meta = src.meta.copy()
        out_meta.update({"driver": "GTiff",
                         "height": out_image.shape[1],
                         "width": out_image.shape[2],
                         "transform": out_transform})

    with rasterio.open(output, "w", **out_meta) as output:
        output.write(out_image)

gdf = gpd.read_file(shp_points)

for i in tqdm(gdf.index):
    for im in tqdm(os.listdir(path_images)):
        if im.endswith('.tif'):
            file = os.path.join(path_images,im)
            # We are using band 2 here, but it could be any band we wish, this will be used just to be the basis of the output dataset.
            img = gdal.Open(file)
            polygon = get_bounds(img)
            gdf.to_crs(img.GetProjection(),inplace=True)
            geometry = gdf['geometry'][i]
            # size_buffer = size/2
            # geometry.buffer(size_buffer)
            x,y = [l[0] for l in geometry.xy]
            geom = create_new_geom(x,y,size,img.GetGeoTransform()[1])

            if polygon.contains(geom):
                output = os.path.join(outpath,os.path.basename(file))
                if os.path.exists(output):
                    clip(file,geom,output)




