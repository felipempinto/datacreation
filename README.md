## datacreation
Repository created to explain how to create dataset from GIS to use with NN.

**download_data.py** -> Explaining how you can download some dataset from sentinel 2 images.

**create_by_geometry.py** -> This file will create the dataset (not the labels) based on sentinel 2 (level 2A) data, and right after it, you will be able to clip the image to the are you wish. It is the first version, so, needs some modifications yet. But the other ones solve this problem.

**crete_imgs.py** -> This one will get the separate bands from sentinel 2 data (level 2A), and join them into a tiff file, you just need to set the path where the ".SAFE" files are stored. 

**createwithsize.py** -> This one will clip the image based on the shapefile with the points and the size of the image you wish to use. if you wish to create an image with 512x512 pixels, for example, this file will get the big image, intersects the point with the area of the image, and create the image with the size you asked.

**create_labels.py** -> This one will be used to create the labels based on OSM dataset.
