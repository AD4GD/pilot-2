import typer
from typing_extensions import Annotated
from rich.console import Console
from rich import print
import os
from protected_areas.wpda_wrapper import WDPAWrapper
from osm.osm_wrapper import OSMWrapper
from enrichment.lulc_enrichment_wrapper import LULCEnrichmentWrapper
from impedance.impedance_wrapper import ImpedanceWrapper

err_console = Console(stderr=True, style="bold red")

app = typer.Typer(
    name="Preprocessing CLI",
    help="CLI tool for preprocessing protected areas and land impedance data.",
)

def check_file_exists(filePath:str):
    """
    Check if a file exists at a given path.

    Args:
        filePath (str): The path to the file.
    """
    if os.path.exists(filePath):
        fileName = os.path.basename(filePath).split(".")[0]
        print(f"[green] {fileName} File found! [/green] :white_check_mark:")
    else:
        err_console.print(f" File not found at {filePath}")
        raise typer.Exit(code=1)

#NOTE only prompt user to confirm using APIs.
@app.command("process-wdpa")
def process_wdpa(
    config_dir: Annotated[str, typer.Option(..., help="directory to the configuration file")] = "./config",
    auto_confirm: Annotated[bool, typer.Option("--force", "-f", help="Auto confirm all prompts")] = False,
    skip_fetch: Annotated[bool, typer.Option("--skip-fetch", "-s", help="Skip fetching protected areas")] = False,
    verbose: Annotated[bool, typer.Option("--verbose", "-v", help="Verbose mode")] = False,
):
    """
    Preprocess protected areas data for each year of lulc data
    Example usage: python main.py process-wdpa --config-dir ./config --force --skip-fetch --verbose
    
    Args:
        config_path (str): The path to the configuration file.
        auto_confirm (bool): Auto confirm all prompts.
        skip_fetch (bool): Skip fetching protected areas data from the API.
        verbose (bool): Verbose mode.
    """
    config_path = os.path.join(config_dir, "config.yaml")
    check_file_exists(config_path)

    try:
        working_dir = os.getcwd()
        wp = WDPAWrapper(working_dir, config_path, verbose=verbose)

        # # STEP 1.0: Get the unique country codes from the LULC raster data
        country_codes = wp.get_lulc_country_codes() # returns {"GBR"} 

        # print to user to confirm country PAs to fetch
        print(f"Country protected areas to fetch: {country_codes}")

        # prompt the user to confirm the countries to fetch.
        if auto_confirm == False:
            confirm = typer.confirm("Type 'yes' or 'y' to confirm API fetch for the above countries?")
            if not confirm:
                err_console.print("Exiting...")
                raise typer.Exit(code=1)
        
        # # STEP 2.0: Fetch and process the protected areas for the selected countries
        print("Fetching protected areas for the selected countries...")
        merged_gpkg = wp.protected_area_to_merged_geopackage(country_codes, "merged_pa.gpkg", skip_fetch)

        # STEP 3.0: Rasterize the merged GeoPackage file
        print("Rasterizing the merged GeoPackage file...")
        wp.rasterize_protected_areas(merged_gpkg, os.path.join(working_dir,wp.config.get("lulc_dir")), pa_to_yearly_rasters=True)
        
        # # STEP 4.0: Raster Calculation
        print("Summing LULC and PA rasters...")
        wp.sum_lulc_pa_rasters()

        # # STEP 5.0: Reclassify input raster with impedance values
        print("Reclassifying the raster with impedance values...")
        wp.reclassify_raster_with_impedance()

        # # STEP 6: Compute affinity
        print("Computing affinity")
        wp.compute_affinity(os.path.join(working_dir, "data", "output", "affinity"))

    except Exception as e:
        err_console.print(f"Error: {e}")
        raise typer.Exit(code=1)

@app.command("process-osm")
def process_osm(
    config_dir: Annotated[str, typer.Option(..., help="directory to the configuration file")] = "./config",
    skip_fetch: Annotated[bool, typer.Option("--skip-fetch", "-s", help="Skip fetching osm data")] = False,
    delete_intermediate_files: Annotated[bool, typer.Option("--del-temp", "-dt", help="Delete intermediate GeoJSON & GPKG files")] = False,
    verbose: Annotated[bool, typer.Option("--verbose", "-v", help="Verbose mode")] = False
    ):
    """
    Check if config exists
    Example usage: python main.py process-osm --config-dir ./config --verbose --skip-fetch --del-temp

    Args:
        config_path (str): The path to the configuration file.
        verbose (bool): Verbose mode.
    """
    config_path = os.path.join(config_dir, "config.yaml")
    check_file_exists(config_path)
    try:
        working_dir = os.getcwd()
        osm = OSMWrapper(working_dir, config_path, verbose)

        # STEP 1: Fetch OSM data
        if not skip_fetch:
            if len(osm.years) > 1:
                #prompt user to confirm which years to fetch
                year = typer.prompt("Type 'all' or enter the year to fetch OSM data from the following years: ", osm.years)
                if year != "all":
                    # repalce the years list with the selected year
                    osm.years = [year]

        # fetch OSM data for the selected years
        osm.osm_to_geojson(osm.years, skip_fetch)

        # STEP 2: Convert OSM data to merged GeoPackage (creates intermediate GeoJSON files for each year)
        osm.osm_to_merged_gpkg(osm.years)
       
        # STEP 3: Delete intermediate files
        if delete_intermediate_files:
            osm.delete_temp_files(delete_geojsons=True, delete_gpkg_files=True)

    except Exception as e:
        err_console.print(f"Error: {e}")
        raise typer.Exit(code=1)
 

@app.command("enrich-lulc")
def enrich_lulc(
    config_dir: Annotated[str, typer.Option(..., help="directory to the configuration file")] = "./config",
    verbose: Annotated[bool, typer.Option("--verbose", "-v", help="Verbose mode")] = False,
    save_osm_stressors: Annotated[bool, typer.Option("--save-osm-stressors", "-s", help="Save OSM stressors to file")] = False
    ):
    """
    Check if config exists
    Example usage: python main.py enrich-lulc --config-dir ./config --verbose --save-osm-stressors

    Args:
        config_path (str): The path to the configuration file.
        verbose (bool): Verbose mode
        save_osm_stressors (bool): Save OSM stressors to file
    """
    config_path = os.path.join(config_dir, "config.yaml")
    check_file_exists(config_path)
    try:
        lew = LULCEnrichmentWrapper(os.getcwd(),config_path,  verbose)

        # prompt user to use all years or a specific year
        if len(lew.years) > 1:
            year = typer.prompt("Type 'all' or enter the year to use for the LULC enrichment from the following years: ", lew.years)
            if year != "all":
                # replace the years list with the selected year
                lew.years = [year]

        # prepare and merge LULC and OSM data
        lew.prepare_lulc_osm_data(lew.years)
        # merge LULC and OSM data
        lew.merge_lulc_osm_data(lew.years, save_osm_stressors)

    except Exception as e:
        err_console.print(f"Error: {e}")
        raise typer.Exit(code=1)

@app.command("recalc-impedance")
def enrich_lulc(
    config_dir: Annotated[str, typer.Option(..., help="directory to the configuration file")] = "./config",
    verbose: Annotated[bool, typer.Option("--verbose", "-v", help="Verbose mode")] = False,
    del_stressors: Annotated[bool, typer.Option("--save-osm-stressors", "-s", help="Delete OSM stressors")] = False,
    decline_type: Annotated[str, typer.Option("--decline-type", "-dt", help="Type of decline to use for impedance calculation. Use either exp_decline OR prop_decline ")] = "exp_decline",
    lambda_decay: Annotated[int, typer.Option("--lambda-decay", "-ld", help="Lambda decay value for impedance calculation")] = 500,
    k_value: Annotated[int, typer.Option("--k-value", "-k", help="K value for impedance calculation")] = 500
    ):
    """
    Check if config exists
    Example usage: python main.py recalc-impedance --config-dir ./config --verbose --save-osm-stressors

    Args:

        config_dir (str): The path to the configuration directory.
        verbose (bool): Verbose mode
        save_osm_stressors (bool): Save OSM stressors to file
    """
    stressor_yaml_path = os.path.join(config_dir,"stressors.yaml")
    if not os.path.exists(stressor_yaml_path):
        raise FileNotFoundError("The stressors.yaml file is not found. Please add the file to the config directory.")
    
    config_path = os.path.join(config_dir, "config.yaml")
    check_file_exists(config_path)
    
    iw = ImpedanceWrapper( 
        types = None,
        decline_type = decline_type,
        lambda_decay = lambda_decay,
        k_value = k_value,
        config_path= config_path,
        config_impedance_path= os.path.join(config_dir,"config_impedance.yaml"),
        verbose=verbose
    )

    # prompt user to use all years or a specific year
    if len(iw.years) > 1:
        year = typer.prompt("Type 'all' or enter the year to use for the LULC enrichment from the following years: ", iw.years)
        if year != "all":
            # replace the years list with the selected year
            iw.years = [year]

    for year in iw.years:
        # 1. Process the impedance configuration (initial setup + lulc & osm stressors)
        # e.g. impedance_stressors = {'primary': '/data/data/output/roads_primary_2018.tif'}
        impedance_stressors = iw.process_impedance_config(year)

    #2. Prompt user to update the configuration file
    typer.secho("Please check/update the configuration file for impedance dataset (config_impedance.yaml):", fg=typer.colors.RED)

    # 2.1. Or validate after manual update 
    is_valid = iw.validate_impedance_config(impedance_stressors)

    if not is_valid:
        raise ValueError("The configuration file is not valid. Please update the configuration file.")
    
    for year in iw.years:
        # 3.  Get the maximum value of the impedance raster dataset
        impedance_ds, impedance_max = iw.get_impedance_max_value(year)

        #3.0 Calculate impedance
        max_result_tif = iw.calculate_impedance(impedance_stressors,impedance_ds,impedance_max)
        if verbose:
            typer.secho(f"max_result_tif saved to: {max_result_tif}", fg=typer.colors.GREEN)

    # delete temporary impedance stressors.yaml
    if del_stressors:
        os.remove(stressor_yaml_path)
        typer.secho("Temporary OSM stressor file has been deleted", fg=typer.colors.RED)

#Test command
@app.command("test")
def init(firstname: str, surname: str, formal: bool = False):
    """
    Example usage 
    python main.py test name surname --formal
    typer run main.py test name surname --formal
    """
    if formal:
        typer.secho(f"Hello Mr. {firstname} {surname}", fg=typer.colors.GREEN, bg=typer.colors.YELLOW)
    else:
        typer.echo(f"Hello {firstname} {surname}")

    err_console.print("This is an error message")



if __name__ == "__main__":
    app()