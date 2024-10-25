This repository is dedicated to the Pilot 2 of the All Data 4 Green Deal (AD4GD) project. <br />
## Sections
- ***Preprocessing*** sub-repository is focused on the enrichment of the input raster land-use/land-cover (LULC) data with vector data from Open Street Map. Protected areas from the World Database on Protected areas are integrated into preprocessing workflow to consider their importance for connecting habitats. This workflow has been translated into the **Data4Land** tool to be considered as a research. The workflow has been described in the Deliverables 6.1 (section 6.7) of the AD4GD project.<br />
- ***Graphab*** sub-repository contains second version of dockerised Graphab Java application partly deployed on the HPC cluster to ensure consistency of environment and to allow the workflow to be run reliably either on a user’s machine or as an open service module (Deliverables 6.1, section 6.7). It is currently being tested for MPI-mode.<br />
- ***GBIF*** sub-repository is focused on the analysis of existing GBIF data (quering, access, provenance and quality of records), corresponding with the Deliverables 6.1 (section 4.6.3, GBIF ingestion). The actual integration of GBIF data with other sources for target species is analysed [here](https://github.com/AD4GD/pilot-2-gbif-iucn). <br />
## Acknowledgement
This activity is part of the AD4GD work, biodiversity pilot: https://ad4gd.eu/biodiversity/. The AD4GD project is co-funded by the European Union, Switzerland and the United Kingdom.





