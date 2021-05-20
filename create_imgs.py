from osgeo import gdal
import os,pathlib
from tqdm import tqdm
gdal.UseExceptions()

path = '/media/felipe/3dbf30eb-9bce-46d8-a833-ec990ba72625/Documentos/Empresa/Upwork/Harald/Project2/data/2A'
outpath = '/media/felipe/3dbf30eb-9bce-46d8-a833-ec990ba72625/Documentos/Empresa/Upwork/Harald/Project2/data/imgs'


def find_band(path,ends):
    # This function is been used to find the bands we wish to use in the dataset.
    return str(list(pathlib.Path(path).rglob(f'*{ends}.jp2'))[0])

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
    dst.FlushCache()


for im in tqdm(os.listdir(path)):
    file = os.path.join(path,im)
    
    out = os.path.join(outpath,os.path.basename(file)+".tif")
    if not os.path.exists(out):
        # We are using band 2 here, but it could be any band we wish, this will be used just to be the basis of the output dataset.
        b2 = gdal.Open(find_band(file,'B02_10m'))
        b3 = gdal.Open(find_band(file,'B03_10m'))
        b4 = gdal.Open(find_band(file,'B04_10m'))
        b8 = gdal.Open(find_band(file,'B08_10m'))

        # We can read the bands like this because I know that these images just have 1 band
        # If the image has more bands, the output will be an array with size (b,x,y) being:
        # b = bands
        # x = x size
        # y = y size
        ar2 = b2.ReadAsArray()
        ar3 = b3.ReadAsArray()
        ar4 = b4.ReadAsArray()
        ar8 = b8.ReadAsArray()
        # UInt16 is the original datatype of Sentinel 2 images. Actually, reflectance values
        # should be lower than 1, but to better store the information, the reflectance is 
        # multiplyied by 10.000, so if you wish to have the real reflectance value, you may
        # divide the bands by 10000.
        create_img(out,b3,[ar2,ar3,ar4,ar8],gdal.GDT_UInt16)
            