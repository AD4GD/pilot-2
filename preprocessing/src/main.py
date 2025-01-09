import typer
from typing_extensions import Annotated
from rich.console import Console
from rich import print
import os
# from protected_areas.WDPAWrapper import WDPAWrapper
# from third_notebook import MyPreprocessor
from protected_areas.wpda_wrapper import WDPAWrapper
import sys

err_console = Console(stderr=True)

app = typer.Typer(
    name="Preprocessing CLI",
    help="CLI tool for preprocessing protected areas and land impedance data.",
)

def check_file_exists(filePath:str):
    """
    Check if a file exists at a given path.
    """
    if os.path.exists(filePath):
        fileName = os.path.basename(filePath).split(".")[0]
        print(f"[green] {fileName} File found! [/green] :thumbsup:")
    else:
        err_console.print(f" File not found at {filePath}", style="bold red")
        raise typer.Exit(code=1)

#NOTE only prompt user to confirm using APIs.
@app.command("process-wdpa")
def process_wdpa(
    config_path: Annotated[str, typer.Option(..., help="Path to the configuration file")] = "./config/config.yaml",
    #auto_confirm: Annotated[bool, typer.Option(False, "--yes", "-y", help="Auto confirm the prompt")] = False
):
    """
    Preprocess protected areas data for each year of lulc data
    Example usage: python main.py process-wdpa --config-path ./config/config.yaml --yes

    Args:
        config_path (str): The path to the configuration file.
        auto_confirm (bool): Auto confirm

    Returns:
        None
    """

    check_file_exists(config_path)

    try:
        working_dir = os.getcwd()
        # # define parent directory (level above)
        # parent_dir = os.path.abspath(os.path.join(current_dir, '..'))
        # # add the parent directory to sys.path
        # sys.path.append(parent_dir)
        
        wp = WDPAWrapper(working_dir, config_path)

        # # STEP 1.0: Get the unique country codes from the LULC raster data
        country_codes = wp.get_lulc_country_codes()

        # print to user to confirm country PAs to fetch
        print(f"Country protected areas to fetch: {country_codes}")

        # prompt the user to confirm the countries to fetch.
        auto_confirm = False
        if auto_confirm == False:
            confirm = typer.confirm("Type 'yes' or 'y' to confirm API fetch for the above countries?")
            if not confirm:
                print("Exiting...")
                raise typer.Exit(code=1)
        
        # # STEP 2.0: Fetch and process the protected areas for the selected countries
        print("Fetching protected areas for the selected countries")
        #TODO change skip_fetch to False
        merged_gpkg = wp.protected_area_to_merged_geopackage(country_codes, "merged_pa.gpkg", skip_fetch=True)

        # STEP 3.0: Rasterize the merged GeoPackage file
        print("Rasterizing the merged GeoPackage file")
        wp.rasterize_protected_areas(merged_gpkg, os.path.join(working_dir,"lulc"), os.path.join(working_dir, "pas_timeseries"), pa_to_yearly_rasters=True)
        
        # # STEP 4.0: Raster Calculation
        print("Raster Calculation")
        wp.sum_lulc_pa_rasters()
        #TODO REMOVE BELOW FROM WP and deprecate from utils.py
        # wp.run_shell_command(os.path.join(current_dir, "raster_sum_loop.sh"))

        # # STEP 5.0: Reclassify input raster with impedance values
        print("Reclassifying the raster with impedance values")
        wp.reclassify_raster_with_impedance()

        # # STEP 6: Compute affinity
        print("Computing affinity")
        wp.compute_affinity()

    except Exception as e:
        err_console.print(f"Error: {e}", style="bold red")
        raise typer.Exit(code=1)

# @app.command("process-osm")
# def process_osm(config_path:Annotated[str, typer.Argument(...)] = "./config.yaml" ):
#     """
#     Check if config exists
#     Example usage: python main.py --config-path ./config.yaml
#     """
#     check_file_exists(config_path)
    
#     # if os.getcwd().endswith("1_protected_areas") == False:
#     #     # NOTE working from docker container
#     #     os.chdir('./1_protected_areas')
#     MyPreprocessor('config.yaml', 'output')
    
#     # wdpa_preprocess(auto_confirm)

# @app.command("process-lulc")
# def process_lulc_enrichment(config_path:Annotated[str, typer.Argument(...)] = "./config.yaml" ):
#     """
#     Check if config exists
#     Example usage: python main.py --config-path ./config.yaml
#     """
#     check_file_exists(config_path)
#     MyPreprocessor('config.yaml', 'output')

#Test command
@app.command()
def init(firstname: str, surname: str, formal: bool = False):
    """
    Example usage 
    python main.py name surname --formal
    """
    if formal:
        typer.secho(f"Hello Mr. {firstname} {surname}", fg=typer.colors.GREEN, bg=typer.colors.YELLOW)
    else:
        typer.echo(f"Hello {firstname} {surname}")

    err_console.print("This is an error message", style="bold red")

if __name__ == "__main__":
    app()