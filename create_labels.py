import geopandas as gpd
from osgeo import gdal,ogr,gdalconst
# import 
import numpy as np
import os
from shapely.geometry import Polygon,MultiPolygon
from tqdm import tqdm

os.chdir(os.path.dirname(os.path.dirname(__file__)))

path = 'data/test'
outpath = 'datasets/labels'
water = 'shps/osm/gis_osm_water_a_free_1.shp'
waterways = 'shps/osm/gis_osm_waterways_free_1.shp'

# this is the dataset of water in polygons of OSM dataset
gdf_water = gpd.read_file(water)
# this is the dataset of water in lines of OSM dataset
gdf_waterways = gpd.read_file(waterways)

#Function to convert to raster a vector file(e.g. shapefile -> tiff)
def rasterize(img,shp,output,atribute,nodata=''):
    # To do this, we need to get the informations from the input image 
    # Informations like n of pixel in x and y, number of bands, projection, pixel size, etc...
    # input variables:
    # -> img: is the base image we will get the information about, we need this to do not need to manually calculate everything.
    # -> shp: the vector file that will be converted to raster file
    # -> output: output name 
    # -> atribute: the columns with the information to convert the data, if you have a column with numbers, the numbers will be converted to pixel values
    # -> nodata: The values that will be ignored.
    data = gdal.Open(img, gdalconst.GA_ReadOnly)
    geo_transform = data.GetGeoTransform()
    proj=data.GetProjection()
    x_min = geo_transform[0]
    y_max = geo_transform[3]
    x_max = x_min + geo_transform[1] * data.RasterXSize
    y_min = y_max + geo_transform[5] * data.RasterYSize
    x_res = data.RasterXSize
    y_res = data.RasterYSize
    mb_v = ogr.Open(shp)
    mb_l = mb_v.GetLayer()
    pixel_width = geo_transform[1]
    target_ds = gdal.GetDriverByName('GTiff').Create(output, x_res, y_res, 1, gdal.GDT_Byte)
    target_ds.SetGeoTransform((x_min, pixel_width, 0, y_min, 0, pixel_width))
    band = target_ds.GetRasterBand(1)
    if nodata!='':
        band.SetNoDataValue(nodata)
    band.FlushCache()
    target_ds.SetProjection(proj)
    gdal.RasterizeLayer(target_ds, [1], mb_l, options=["ATTRIBUTE="+atribute])
    target_ds = None

def create_img(output,img,array,dtype = gdal.GDT_UInt16):
    driver = gdal.GetDriverByName("GTiff")
    dst = driver.Create(output,img.RasterXSize,img.RasterYSize,len(array),dtype)
    for i in range(len(array)):
        b = dst.GetRasterBand(i+1)
        b.WriteArray(array[i])
    dst.SetProjection(img.GetProjection())
    dst.SetGeoTransform(img.GetGeoTransform())
    dst.FlushCache()

def get_bounds(img):
    # To get the boundaries of the image
    minx, xres, _, maxy, _, yres  = img.GetGeoTransform()
    maxx = minx + (img.RasterXSize * xres)
    miny = maxy + (img.RasterYSize * yres)
    return Polygon([[minx,maxy],[maxx,maxy],[maxx,miny],[minx,miny]])

# looping through all the images
for i in tqdm(os.listdir(path)):
    if i.endswith(".tif"):
        f = os.path.join(path,i)
        out = os.path.join(outpath,i)
        output_img = os.path.join(os.path.dirname(outpath),'inputs',i)
        img = gdal.Open(f)
 
        if not os.path.exists(output_img):
            # This line is just to create a copy of the input image into the folder called "inputs"
            create_img(output_img,img,img.ReadAsArray())

        if not os.path.exists(out):
            # the variable "poly" will be the boundaries of the image
            # the reason to get this is to just select the water bodies of the area we are looking for.
            poly = get_bounds(img)
            gdf_water.to_crs(img.GetProjection(),inplace=True)
            gdf_waterways.to_crs(img.GetProjection(),inplace=True)
            # here we are selecting the geometries that intersects or contains the image
            g = gdf_water[(gdf_water.intersects(poly) | gdf_water.contains(poly))]
            g2 = gdf_waterways[(gdf_waterways.intersects(poly) | gdf_waterways.contains(poly))]
            polygons = []
            if len(g)>0:
                # If there is polygons inside the image
                g['dis'] = [0]*len(g)
                # The dissolve function will join all the geometries.
                g = g.dissolve('dis') 
                p = g['geometry'][g.index[0]]
                polygons.append(p)
            elif len(g2)>0:
                g2['geometry'] = g2.buffer(10)
                g2['dis'] = [0]*len(g2)
                g2 = g2.dissolve('dis')
                p = g2['geometry'][g2.index[0]]
                polygons.append(p)

            if len(polygons)>0:
                #Now, we will join all polygons
                try:
                    waters = MultiPolygon(polygons)
                except ValueError:
                    if len(polygons)==1:
                        waters = polygons[0]
                    else:
                        raise ValueError("Problem during the process")
                ggdf = gpd.GeoDataFrame(geometry = [waters],crs = img.GetProjection())
                ggdf['dis'] = [1]*len(ggdf)
                if len(polygons)>1:
                    ggdf = ggdf.dissolve('dis')
                ggdf.to_file("temp.shp")
                rasterize(f,'temp.shp',out,'dis')
                os.remove('temp.shp')

            else:
                # If there is no water bodies, the labeled image will have just 0 values.
                array = np.zeros((img.RasterXSize,img.RasterYSize))
                create_img(out,img,[array],gdal.GDT_Byte)
        



