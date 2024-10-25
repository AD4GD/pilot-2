### Data4Land - enrichment of land-use/land-cover (LULC) data
This preprocessing workflow currently includes three separate Jupyter Notebooks (four with optional Notebook for habitat connectivity study):

- **[Enrichment with data on protected areas](1_protected_areas/1_preprocessing_pas.ipynb)**
Available only through the authorised credentials (token), as it uses the special API. ***OPTIONAL***
- **[Fetching historical vector data](2_osm_historical.ipynb)**
Available without authorised credentials, uses open-access API. ***MANDATORY***
- **[Rewriting and harmonising input data](3_preprocessing.ipynb)**
Preprocessing itself – reprojection, checking, rewriting raster files etc. ***MANDATORY***
- **[Applying edge effect to stressors for habitat connectivity](4_impedance.ipynb) ***OPTIONAL***

Detailed descriptions of each nested workflow are given at the beginnings of Jupyter Notebooks.

The workflow can be also explored on the overarching diagram:![diagram](visualisation/workflow.png)

#### Current state

This tool is mostly completed, but a few improvements are planned to be completed in new versions:

- Design command-line tool in addition to the separate Notebooks.
- Test [ohsome API](https://docs.ohsome.org/ohsome-api/v1/) again to find out if it spossible to filter out attributes directly within queries and reduce the execution time. If so, it makes sense to move to ohsome API instead of Overpass Turbo API. See [issue](https://github.com/GIScience/ohsome-api/issues/332).
- Complete cumulative statistics for deprecated and new tags for Catalonia and UK through ohsome API.
- Replace NULL values of 'width' for roads and railways with self-defined width in SQL queries.
- Implement [VRT](https://gdal.org/en/latest/drivers/raster/vrt.html) file format if possible to save resource.
- WDPA API: For LULC codes covered by protected areas, define the multiplier of impedance (effect of protected areas), cast to the yaml file and automatically estimate impedance value.
- For use case study: revisit Catalonian government data on ecological barriers and decide on its usage.
- For use case study: implement other datasets, such as [small woody patches](https://land.copernicus.eu/en/products/high-resolution-layer-small-woody-features) that can be used by species as 'stepping stones' to migrate between habitats.
