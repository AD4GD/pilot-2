## **Data4Land** tool - enriching land-use/land-cover with historical vector(s) data (v.2.0.0)

Data4Land tool is developed to enrich various land-use/land-cover (LULC) spatial data with data from another sources to increase the consistency and reliability of LULC datasets for multiple purposes. This software currently includes four independent components which can be run in command-line interface (CLI):

1. **[Access to historical data from the World Database on Protected Areas (WDPA) and data harmonization](protected_areas/)**
Available only through the authorised credentials (token), as it uses the special API. Jupyter Notebook format with detailed documentation is available [here](1_pas.ipynb).
2. **[Access and harmonisation of historical LULC data in vector - Open Street Map (OSM) data ](osm/)**
Freely available without authorised credentials, uses open-access API. Jupyter Notebook is available [here](2_vector.ipynb).
3. **[Enrichment of LULC data](enrichment/)**
Enhancing of initial LULC data with supplementary data from 1st and 2nd blocks, or user-defined data. Jupyter Notebook is available [here](3_enrichment.ipynb).
4. **[Impedance calculation ('edge effect' of biodiversity stressors)](impedance/)**
Calculates 'landscape impedance' datasets based on user-defined biodiversity stressors. This component is useful for researchers to conduct follow-up studies on nature conservation and habitat connectivity. Jupyter Notebook is available [here](4_impedance.ipynb).

Detailed documentation on each nested component is given at the beginnings of corresponding Jupyter Notebooks and includes descriptions of all input and output datasets valid for v 1.0.0.

Sample input datasets are different for v1.0.0 and v2.0.0.
**v1.0.0**
Sample dataset is from [ESA Sentinel-2 World Cover](https://collections.sentinel-hub.com/impact-observatory-lulc-map/) remote sensing collections, covering a part of Northern England, located [here](data/input/).
**v2.0.0**
- From the [land-use/land-cover map of Catalonia (MCSC)](https://www.opengis.grumets.cat/MCSC) with 7 LULC types, covering the whole of Catalonia, located [here](src/data/cat_aggr_buf_30m).
- The subdataset of MCSC Catalonia, covering only the small north-eastern part, but including 24 LULC types, located [here](src/data/case_study_albera).
As input LULC datasets can be potentially used across multiple sub case studies, they are located in the [shared](src/data/shared).
Therefore, Data4Land provides scalable solution to enrich LULC datasets with different spatial extent and level of granularity.

All configuration to execute the components of Data4Land tool is pre-defined for the sample dataset in the [configuration YAML file](src/config/config.yaml): paths, filenames, API parameters, and user-defined numerical parameters.
The v.2.0.0 supports **case studies** and **sub case studies**. For example, user would like to run Data4Land tool for completely different LULC datasets in Catalonia and England. In this case, user must specify `case_study_dir` in the [configuration file](src/config/config.yaml), for example, `case_study_dir: 'catalonia'`, as Catalonia and England have completely independent LULC datasets.

Also, there might be the same LULC datasets for one case study area, for example, covering Catalonia in 2012-2022, but user would like to execute them with different landscape impedance (or resistance) parameter. In this case they must provide the series of landscape impedance datasets for each **sub case study** and define it in the configuration file, for example, `sub_case_study: 'forest'` or `sub_case_study: 'meadows'` to calculate outputs for different LULC types. User is free to define sub case studies for other objects, aside from LULC types, for example, for species: `sub_case_study: 'turtle'`. However, it is crucial to provide the relevant landscape impedance datasets for each sub case study, putting them to the following path: `src/data/**case_study**/input/**sub_case_study**_impedance/`. See the example of configured path [here](src/data/cat_aggr_buf_30m/input/forest_impedance/).
The **sub case study** differentiation is relevant for the 4th component only.

Data flow within the Data4Land tool can be also explored on the overarching diagram:![diagram](visualisation/cli_workflow.png).

### Usage and command references

The Data4Land tool should be run within the container environment. To create the container, run:
`docker-compose up`
It will build the container with the necessary requirements.

Inside the created container environment, use the following prompt structure:
`main.py [OPTIONS] COMMAND [ARGS]...`

To see the available commands, type `python main.py --help`.

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
**Description**: preprocess data on protected areas from the World Database on Protected Areas (WDPA) for each year of LULC data.
**Example usage**:
```bash
 python main.py process-wdpa --config-dir ./config --force --skip-fetch --del-temp --verbose --record-time
```
**Arguments**:
- config_dir (str): Directory containing the configuration file. Aliases: --config-dir.
- use_yearly_pa_raster (bool): Use less than or equal to PA year of establishment when TRUE, else use all years. Aliases: "--enrich-single-year", "-e".
- auto_confirm (bool): Auto confirm all prompts. Aliases: "--force", "-f".
- skip_fetch (bool): Skip fetching protected areas data from the API if the data already exists in the shared input directory. Aliases: "--skip-fetch", "-s"
- delete_intermediate_files (bool): Delete intermediate GPKG files. Aliases: "--del-temp", "-dt".
- verbose (bool): Verbose mode. Enable, if you wish to see explicitly all the steps in processing. Aliases: "--verbose", "-v".
- record_time (bool): Record the execution time. Aliases: "--record-time", "-t".

***2. process-osm***
**Description**: fetches and translates data from OpenStreetMap database.
**Example usage**: 
```bash
python main.py process-osm --config-dir ./config --api ohsome --verbose --skip-fetch --del-temp --record-time
```
**Arguments**:
- config_dir (str): Directory containing the configuration file. Aliases: "--config_dir".
- api_type (str): API to use for fetching OSM data. Choose from 'overpass' or 'ohsome. Aliases: "--api", "-a".
- skip_fetch (bool): Skip fetching OSM data. Overwrites existing data if FALSE. Aliases: "--skip-fetch", "-s".
- delete_intermediate_files (bool): Delete intermediate GeoJSON & GPKG files. Aliases: "--del-temp", "-dt".
- verbose (bool): Verbose mode. Enable, if you wish to see explicitly all the steps in processing. Aliases: "--verbose", "-v".
- record_time (bool): Record the execution time. Aliases: "--record-time", "-t".

***3. enrich-lulc***
**Description**: processes and merges fetched OpenStreetMap data into output LULC dataset. 
**Example usage**:
```bash
python main.py enrich-lulc --config-dir ./config --verbose --save-osm-stressors
```
**Arguments**:
- config_dir (str): Directory containing the configuration file. Aliases: "--config_dir".
- api_type (str): API to use for fetching OSM data. Choose from 'overpass' or 'ohsome' or leave blank if none were used.Aliases: "--api", "-a".
- threads (int): Number of threads to use for processing (default is 4). Aliases: "--threads", "-t".
- verbose (bool): Verbose mode. Enable, if you wish to see explicitly all the steps in processing. Aliases: "--verbose", "-v".
- save_osm_stressors (bool): Save OSM stressors to file. Aliases: "--save-osm-stressors", "-s".
- record_time (bool): Record the execution time. Aliases: "--record-time", "-t".

***4. recalc-impedance***
**Description**: recalculates landscape impedance data for follow-up computations.
**Example usage**:
```bash
python main.py recalc-impedance --config-dir ./config --verbose --del-stressors
```
**Arguments**:
- config_dir (str): The path to the configuration directory. Aliases: "--config_dir".
- verbose (bool): Verbose mode. Enable, if you wish to see explicitly all the steps in processing. Aliases: "--verbose", "-v".
- del_stressors (bool): Delete OSM stressors (intermediate GeoTIFF files). Aliases: "--del-stressors", "-s".
- decline_type (str): Type of decline to use for impedance calculation. Use either exp_decline OR prop_decline. Aliases: "--decline-type", "-dt".
- lambda_decay (int): Lambda decay value for impedance calculation (if decline type is exponential). Aliases: "--lambda-decay", "-ld".
- k_value (int): K-value for impedance calculation (if decline type is proportional). Aliases: "--k-value", "-k".
- record_time (bool): Record the execution time. Aliases: "--record-time", "-t".

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

In v.2.0.0, user can specify whether they would like to use [Overpass Turbo](https://wiki.openstreetmap.org/wiki/Overpass_turbo) or [ohsome API](https://docs.ohsome.org/ohsome-api/v1/) to fetch OSM data. Ohsome API is recommended, as it is more stable and provides quicker fetching, especially for multiple timestamps.

**3d**:
```bash
python main.py enrich-lulc --config-dir ./config --verbose --save-osm-stressors
```
This component enriches the input land-use/land-cover (LULC) dataset with the fetched OSM data.
If user would like to execute the 4th component later on, they should enable `--save-osm-stressors` to use these intermediate GeoTIFF outputs (biodiversity stressors) in the recalculation of landscape impedance. However, the enabled parameter will require additional time to process the stressors.

**4th**:
```bash
python main.py recalc-impedance --config-dir ./config --verbose
```
If users enable `--del-stressors` intermediate GeoTIFF files will be deleted. If you would like to explore these files to check the consistency of computation or debug the process, you should disable `--del-stressors`.

While executing this command, you will see the warning asking you to check and update the configuration on the biodiversity stressors. By default, Data4Land creates the sample parameters for each stressors, but in reality users will highly likely put other values depending on their expertise, empirical knowledge of ecological parameters, or bibliography. For example, roads and railways could be considered to have exponential character of decline, but have different values of decline parameter.

The custom configuration of parameters used for the sample data in Catalonia and Northern England [here](src/config/config_examples).

**Warning**: if you delete stressors, you would have to calculate them again using the 3d command.

#### Further development
This tool is mostly completed, but a few improvements are planned to be done:

- Extend the implementation of [VRT](https://gdal.org/en/latest/drivers/raster/vrt.html) file format to save resource.
- Implement ingestion of other spatial features in raster format which may act opposed to biodiversity stressors, for example, [small woody features](https://land.copernicus.eu/en/products/high-resolution-layer-small-woody-features.)
- Implement AI agent for on-fly construction of queries to OSM database from the user input and follow-up enrichment of LULC datasets (supposedly through Natural Language Processing model).

#### Impact
The example of follow-up calculations of habitat connectivity based on non-enriched and enriched LULC datasets is given [here](stats/) to illustrate the significant impact of enriched raster pixels even if a small share of pixels is modified by vector data.

#### Acknowledgement
This software is the part of the [AD4GD project, biodiversity pilot](https://ad4gd.eu/biodiversity/). The AD4GD project is co-funded by the European Union, Switzerland and the United Kingdom (UK Research and Innovation).

#### Licence
See [licence file](LICENSE.txt) for details.