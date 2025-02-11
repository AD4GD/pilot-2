## **Data4Land** tool - enriching land-use/land-cover with historical vector(s) data

Data4Land tool is developed to enrich various land-use/land-cover (LULC) spatial data with data from another sources to increase the consistency and reliability of LULC datasets for multiple purposes. This software currently includes four independent components which can be run in command-line interface (CLI):

1. **[Access to historical data from the World Database on Protected Areas (WDPA) and data harmonization](protected_areas/)**
Available only through the authorised credentials (token), as it uses the special API. Jupyter Notebook format with detailed documentation is available [here](1_pas.ipynb).
2. **[Access and harmonisation of historical LULC data in vector - Open Street Map (OSM) data ](osm/)**
Available without authorised credentials, uses open-access API. Jupyter Notebook is available [here](2_vector.ipynb).
3. **[Enrichment of LULC data](enrichment/)**
Rectification of commonly produced LULC raster data with auxiliary data from 1st and 2nd blocks, or user-defined data. Jupyter Notebook is available [here](3_enrichment.ipynb).
4. **[Impedance calculation ('edge effect' of biodiversity stressors)](impedance/)**
Calculates 'landscape impedance' datasets based on user-defined biodiversity stressors. This component is useful for researchers to proceed with habitat connectivity studies. Jupyter Notebook is available [here](4_impedance.ipynb).

Detailed documentation on each nested component is given at the beginnings of corresponding Jupyter Notebooks and includes descriptions of all input and output datasets valid for v 1.0.0.
Sample input dataset is extracted from [ESA Sentinel-2](https://collections.sentinel-hub.com/impact-observatory-lulc-map/) remote sensing collections and located [here](data/input/).
All configuration to execute the components of Data4Land tool is pre-defined for the sample dataset in the [configuration YAML file](src/config/config.yaml): paths, filenames, API parameters, and user-defined numerical parameters.
Data flow within the Data4Land tool can be also explored on the overarching diagram:![diagram](visualisation/cli_workflow.png).

### Usage and command references

The Data4Land tool must be run within the container environment. To create the container, run:
`docker-compose up`
It will build the container with the necessary requirements.

Inside the created container environment, use the following prompt structure:
`main.py [OPTIONS] COMMAND [ARGS]...`

To see the available commands, 

### Command references and options

Five commands are available, which reflect the four Data4Land components and one test command:
```
process-wdpa
process-osm
enrich-lulc
recalc-impedance
test
```

***1. process-wdpa***
**Description**: preprocess data on protected areas for each year of LULC data.
**Example usage**:
```bash
python main.py process-wdpa --config-dir ./config --force --skip-fetch --verbose
```
**Arguments**:
-config_dir (str): Directory containing the configuration file.
-force (bool): Auto confirm all prompts.
-skip_fetch (bool): Skip fetching protected areas data from the API.
-verbose (bool): Verbose mode.
-record_time (bool): Record the execution time

***2. process-osm***
**Description**: Fetches and translates Open Street Map data.
**Example usage**: 
```bash
python main.py process-osm --config-dir ./config --verbose --del-temp
```
**Arguments**:
-config_dir (str): Directory containing the configuration file.
-skip_fetch (bool): Skip fetching OSM data.
-delete_intermediate_files (bool): Delete intermediate GeoJSON & GPKG files.
-verbose (bool): Verbose mode.
-record_time (bool): Record the execution time.

***3. enrich-lulc***
**Description**: Processes and merges fetched data into output LULC dataset. 
**Example usage**:
```bash
python main.py enrich-lulc --config-dir ./config --verbose --save-osm-stressors
```
**Arguments**:
-config_dir (str): Directory containing the configuration file.
-verbose (bool): Verbose mode.
-save_osm_stressors (bool): Save OSM stressors to file.
-record_time (bool): Record the execution time.

***4. recalc-impedance***
**Description**: Recalculates landscape impedance data for follow-up commputations.
**Example usage**:
```bash
python main.py recalc-impedance --config-dir ./config --verbose --del-stressors
```
**Arguments**:
-config_dir (str): The path to the configuration directory.
-verbose (bool): Verbose mode
-del_stressors (bool): Delete OSM stressors (intermediate GeoTIFF files).
-decline_type (str): Type of decline to use for impedance calculation. Use either exp_decline OR prop_decline.
-lambda_decay (int): Lambda decay value for impedance calculation (if decline type is exponential).
-k_value (int): K-value for impedance calculation (if decline type is proportional).
-record_time (bool): Record the execution time.


### Examples

To test if your instance of Data4Land is configured correctly, execute the test command:
```bash
python main.py user_name user_surname --formal
```
It will render: 
`Hello Mr. user_name user_surname`

To execute the **1st component**, run:
```bash
python main.py process-wdpa --config-dir ./config --force --verbose
```
We do not recommend to change the name and path to the configuration file. Verbose mode will show the whole log of operations behind the command-line tool, and it is recommended to enable it if troubleshooting required.

`--force` mode for this command will automatically say 'yes' to the following promt after printing the codes of countries intersecting the bounding box of input raster:
`Type 'yes' or 'y' to confirm API fetch for the above countries?"`

**2nd component**:
```bash
python main.py process-osm --config-dir ./config --verbose --del-temp
```
It is usually recommended to enable --del-temp if you are working with multiple LULC rasters in Data4Land tool. Otherwise, rewriting conflicts and adding new features to previous GeoJSON and GeoPackage files are possible.

`--force` mode for this command will automatically say 'all' to the following prompt after printing the years configured to fetch OSM data:
`Type 'all' or enter the year to fetch OSM data from the following years: "`

It is planned that once [ohsome API](https://docs.ohsome.org/ohsome-api/v1/) is implemented, users can specify under the new option whether they would like to use [Overpass Turbo](https://wiki.openstreetmap.org/wiki/Overpass_turbo) or ohsome API to fetch OSM data.

**3d**:
```bash
python main.py enrich-lulc --config-dir ./config --verbose --save-osm-stressors
```
If users would like to execute the 4th component, they should enable `--save-osm-stressors` to use these intermediate GeoTIFF outputs in the recalculation of landscape impedance.

**4th**:
```bash
python main.py recalc-impedance --config-dir ./config --verbose
```
If users enable `--del-stressors` intermediate GeoTIFF files will be deleted. If you would like to explore these files to check the consistency of computation or debug the process, you should disable `--del-stressors`.

While executing this command, you will see the warning asking you to check and update the configuration on the biodiversity stressors. By default, Data4Land creates the sample parameters for each stressors, but in reality users will highly likely put other values depending on their expertise and knowledge of ecological parameters. For example, roads and railways could be considered to have exponential character of decline, but have different values of decline parameter.

The custom configuration of parameters used for the sample ESA data in Northern England can be explored [here](config/config_impedance_esa_example.yaml).

**Warning**: if you delete stressors, you would have to calculate them again using the 3d command.

#### Further development
This tool is mostly completed, but a few improvements are planned to be done:

- Implement [ohsome API](https://docs.ohsome.org/ohsome-api/v1/) instead of Overpass Turbo APO as it provides a quicker and more reliable access, as well as publish tests on execution time.
- Extend the implementation of [VRT](https://gdal.org/en/latest/drivers/raster/vrt.html) file format to save resource.
- Implement ingestion of other spatial features in raster format which may act opposed to biodiversity stressors, for example, [small woody features](https://land.copernicus.eu/en/products/high-resolution-layer-small-woody-features.)
- Implement iterations over multiple LULC files (by year and location) and multiple OSM requests (iterating over the combination of filename-yearname).

#### Impact
The example of follow-up calculations of habitat connectivity based on non-enriched and enriched LULC datasets is given [here](stats/) to illustrate the significant impact of enriched raster pixels even if a small share of pixels is modified by vector data.

#### Acknowledgement
This software is the part of the [AD4GD project, biodiversity pilot](https://ad4gd.eu/biodiversity/). The AD4GD project is co-funded by the European Union, Switzerland and the United Kingdom (UK Research and Innovation).

#### Licence
See [licence file](LICENSE.txt) for details.