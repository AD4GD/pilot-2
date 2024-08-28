### Enrichment of land-use/land-cover (LULC) data

The preprocessing workflow currently includes three separate Jupyter Notebooks:

- *[Enrichment with data on protected areas](preprocessing/1_preprocessing_pas.ipynb)*
Available only through the authorised credentials (token), as it uses the special API (should be an optional module).
- *[Fetching historical vector data](2_osm_historical.ipynb)*
Available without authorised credentials, uses open-access API (mandatory).
- *[Rewriting and harmonising input data](3_preprocessing.ipynb)*
Preprocessing itself – reprojection, checking, rewriting raster files etc. (mandatory)

Detailed descriptions of each nested workflow are given in the heads of Jupyter Notebooks.

#### Current state

This tool is mostly completed, but a few improvements are planned to be done:

-**Design user-friendly GUI tool (maybe, semi-automatic) instead of separate Notebooks/scripts and prepare for the publication.**
-**Implement Common Workflow Language (CWL).**
- Implement [VRT](https://gdal.org/en/latest/drivers/raster/vrt.html) file format if possible to save resource.
- Test [ohsome API](https://docs.ohsome.org/ohsome-api/v1/) again to prove that not all attributes of OSM features can be fetched and justify the usage of Overpass Turbo API instead of ohsome API.
- Complete statistics for deprecated and new tags for Catalonia and UK through ohsome API.
- Create a few options of 'decay rate' (from specific categories of land use, 'stressors') expressions for user to choose from.
- Replace NULL values of 'width' for roads and railways with self-defined width in SQL queries.
- WDPA API: iterate over the pages of the response and concatenate to the final response.
