from osgeo import gdal
import os
import pathlib
from tqdm import tqdm
import numpy as np
import rasterio
from shapely.geometry import Polygon
from rasterio.mask import mask
import geopandas as gpd

#The file with the locations you need to create the dataset
shp = ''
#The path of the input images.
images = ''
#Location to save the images
outpath = ''


def create_img(output,img,array,dtype = gdal.GDT_UInt16):
    '''
    To be able to create a new image, you need to have a input image where the data
    will be get from. 
    output = output name of the image
    img = image base to create the new one.
    array = arrays of the bands of the new image
    '''
    driver = gdal.GetDriverByName("GTiff")
    dst = driver.Create(output,img.RasterXSize,img.RasterYSize,len(array),dtype)
    for i in range(len(array)):
        b = dst.GetRasterBand(i+1)
        b.WriteArray(array[i])
    dst.SetProjection(img.GetProjection())
    dst.SetGeoTransform(img.GetGeoTransform())
    dst.FlushCache() #this is needed to save the image

def find_band(path,ends):
    return str(list(pathlib.Path(path).rglob(f'*{ends}.jp2'))[0])

def get_bounds(img):
    minx, xres, _, maxy, _, yres  = img.GetGeoTransform()
    maxx = minx + (img.RasterXSize * xres)
    miny = maxy + (img.RasterYSize * yres)
    return Polygon([[minx,maxy],[maxx,maxy],[maxx,miny],[minx,miny]])

def get_bounds_shp(geometry):
    minx,miny,maxx,maxy = geometry.bounds
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


gdf = gpd.read_file(shp)


for g in gdf.index:
    geometry = gdf['geometry'][g]
    ident = gdf['gppd_idnr'][g]
    
    for i in os.listdir(images):
        if i.endswith(".SAFE"):
            path = os.path.join(images,i)
            b3 = gdal.Open(find_band(path,'B03_10m'))
            gdf.to_crs(b3.GetProjection(),inplace=True)
            polygon = get_bounds(b3)
            
            if polygon.contains(geometry):
                b8 = gdal.Open(find_band(path,'B08_10m'))
                ar3 = b3.ReadAsArray().astype('float32')
                ar8 = b8.ReadAsArray().astype('float32')

                array = (ar3-ar8)/(ar3+ar8)
                
                out = path+"_NDWI.tif"
                if not os.path.exists(out):
                    create_img(out,b3,[array],gdal.GDT_Float32)
                
                output = os.path.join(outpath,ident+'_'+i[11:19]+'.tif')
                if not os.path.exists(output):
                
                    geo = get_bounds_shp(geometry)
                    clip(out,geo,output)
