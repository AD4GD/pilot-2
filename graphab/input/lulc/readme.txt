# These files are COG-formatted TIFFs of land-use/land-cover with a buffer of 30 km from the Catalonian border 
# They have been obtained through gdal_translate ("-of COG -co COMPRESS=LZW")



gdal_translate -ot Float64 -of COG -co COMPRESS=LZW C:\Users\kriukovv\Documents\Graphab\outputs\IF_2022.tif C:\Users\kriukovv\Documents\Graphab\outputs\IF_COG_2022.tif

gdal_translate -ot Int16 -of COG -co COMPRESS=LZW C:\Users\kriukovv\Documents\Graphab\outputs\corridors\*.tif C:\Users\kriukovv\Documents\Graphab\outputs\corridors_cog\*.tif
