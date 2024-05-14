This workflow to enrich existing LULC raster data with vector data on protected areas can be accessed through the Jupyter Notebook ("preprocessing_pas.ipynb") with links to separate scripts. It is planned to develop this code further to access data from WDPA semi-automatically.

The following input data are mandatory:
- Directory "lulc" with file pattern "lulc_xxxx" where xxxx-year
- Geopackage "pas" deriving from WDPA
- Reclassification CSV table with two columns:
	1. lulc (integer)
	2. impedance (integer/float)