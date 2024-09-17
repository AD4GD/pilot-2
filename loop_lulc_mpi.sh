# to set cd: "cd c:\Users\kriukovv\Documents\Graphab\test_hpc_2"
# ! TO RUN this code use: 
# chmod +x loop_lulc_mpi.sh
# ./loop_lulc_mpi.sh

# this native MPI mode relies on OpenMPI mode and JDK
# to install it on Ubuntu VM, the following worked:
# sudo apt-get install openmpi-bin libopenmpi-dev

# to set directory with lulc files
lulc_path="input/lulc"

# to list all lulc files in the directory
lulc_files=("$lulc_path"/*.tif)

# other parameters 
# to pull a list of LULC types to $habitat_forests variable
# TODO - ideally to pull a list of corresponding codes from csv table with matching (for example, 1,2,3,4 codes are merged and transformed into 1)
habitat_forests=("6")
meadows_shrublands=("13,14,15,16,22")
herb_crops=("8,9,24")
woody_crops=("10,11,12,25")
aqua=("1,20")

# additional parameters
# merge - this option has been chosen by default
nodata=0
minarea=30
maxdist=2355
# con8 - this option has been omitted (takes extra time to compute)

# to loop through each GeoTIFF file
for lulc_file in "${lulc_files[@]}"; do
    # to extract year from the LULC file name - 4 numbers
    lulc_numbers=$(echo "$lulc_file" | grep -oP '\d{4}')

    # to print names of files and years
    echo "LULC File: $lulc_file"
    echo "Extracted Year: $lulc_numbers"

    # to find corresponding impedance file based on the extracted year
    impedance_file="input/impedance/impedance_lulc_${lulc_numbers}.tif"
    echo "Impedance File: $impedance_file"

    echo "Current Directory: $(pwd)"

     create a directory for outputs
    mkdir -p output

    # to find corresponding Graphab project name based on the extracted year
    test_loop="connectivity_${lulc_numbers}"
    # to call out projects already created
    test_loop_upd="output/connectivity_${lulc_numbers}/connectivity_${lulc_numbers}.xml"

    # to check if the impedance file exists before proceeding
    if [ -f "$impedance_file" ]; then
        # construct command
        # TODO - add --corridor flag for looping

        # to construct the first part of command in non-mpi mode (as not every -flag is supported by mpi)
        command_non_mpi="java -jar graphab-2.8.6.jar --create $test_loop $lulc_file habitat=$habitat_forests nodata=$nodata minarea=$minarea dir=output --linkset distance=cost name=cost_2355 maxcost=$maxdist extcost=$impedance_file --graph threshold=$maxdist"
       
        echo "Executing Command: $command_non_mpi"

        # run command in non-mpi mode
        $command_non_mpi

        # check the exit status of the last command
        if [ $? -eq 0 ]; then
            echo "Command_non_mpi for $lulc_file completed successfully."
        else
            echo "Error: Command_non_mpi for $lulc_file encountered an issue."
        fi

        # to construct the second part of command in mpi mode
        command_mpi="mpirun java -jar graphab-2.8.6.jar -mpi --project $test_loop_upd --lmetric IF d=$maxdist p=0.05 beta=1"

        echo "Executing Command: $command_mpi"

        # run command in mpi mode
        $command_mpi

         # check the exit status of the last command
        if [ $? -eq 0 ]; then
            echo "Command_mpi for $lulc_file completed successfully."
        else
            echo "Error: Command_mpi for $lulc_file encountered an issue."
        fi

    else
        echo "Error: Impedance file $impedance_file not found for $lulc_file"
    fi

    echo "-----------------------------"
done

