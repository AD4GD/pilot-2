# to set directory with lulc files
lulc_path="input/lulc"

# to list all lulc files in the directory
lulc_files=("$lulc_path"/*.tif)

# other parameters 
# to pull a list of LULC types to $habitat_forests variable - developed for LULC maps of Catalonia so far
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

# COMMAND №1 (!has been already deployed)
command_1="java -jar graphab-2.8.6.jar --create graphab_test input/lulc/lulc_1987.tif habitat=6 nodata=0 minarea=0.1 dir=output --capa area"
# check the exit status of the command
        if [ $? -eq 0 ]; then
            echo "Success: $command_1 completed."
        else
            echo "Error: $command_1 encountered an issue."
        fi

echo "Executing Command: $command_1"
# run command
$command_1

# COMMAND №2
command_2="java -jar graphab-2.8.6.jar --create graphab_test input/lulc/lulc_1987.tif habitat=6 nodata=0 minarea=30 dir=output --capa area --linkset distance=cost name=cost_500 maxcost=500 extcost=input/impedance/impedance_lulc_1987.tif --graph threshold=400:100:500 --lmetric IF d=400:100:500 p=0.05 beta=1"
# check the exit status of the command
        if [ $? -eq 0 ]; then
            echo "Success: $command_2 completed."
        else
            echo "Error: $command_2 encountered an issue."
        fi

echo "Executing Command: $command_2"
# run command
$command_2

# COMMAND №3
command_3="java -jar graphab-2.8.6.jar --project output/graphab_test.xml --delta PC d=600 p=0.05 beta=1 obj=patch"
# check the exit status of the command
        if [ $? -eq 0 ]; then
            echo "Success: $command_3 completed"
        else
            echo "Error: $command_3 encountered an issue."
        fi

echo "Executing Command: $command_3"
# run command
$command_3

# COMMAND №4
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

    # to find corresponding Graphab project name based on the extracted year
    test_loop="output/connectivity_${lulc_numbers}"

    # to check if the impedance file exists before proceeding
    if [ -f "$impedance_file" ]; then
        # construct command
        # TODO - add -- corridor option for looping
        command_4="java -jar graphab-2.8.6.jar --create $test_loop $lulc_file habitat=$habitat_forests nodata=$nodata minarea=$minarea dir=output --linkset distance=cost name=cost_2355 maxcost=$maxdist extcost=$impedance_file --graph threshold=$maxdist --lmetric IF d=$maxdist p=0.05 beta=1"
       
        # a follow-up command to compute corridors based on this distance (--project flag might be wrong) 
        # command="java -jar graphab-2.8.6.jar --project ${test_loop}.xml --corridor maxcost=$maxdist format=raster beta=1 d=$maxdist p=0.05
        
        echo "Executing Command: $command_4"

        # run command
        $command_4

        # check the exit status of the command
        if [ $? -eq 0 ]; then
            echo "Success: $command_4 for $lulc_file completed successfully."
        else
            echo "Error: $command_4 for $lulc_file encountered an issue."
        fi
    else
        echo "Error: Impedance file $impedance_file not found for $lulc_file"
    fi

    echo "-----------------------------"
done

