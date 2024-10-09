# syntax=docker/dockerfile:1
FROM amazoncorretto:latest as base
WORKDIR /app

# to install the necessary packages
RUN sudo apt-get install openmpi-bin libopenmpi-dev

COPY graphab-2.8.6.jar graphab-2.8.6.jar 

# to create folders with input data
RUN mkdir /app/input
RUN mkdir /app/input/lulc/
RUN mkdir /app/input/impedance/ 

# to copy the content of folders with input data
COPY input/lulc/*.tif /app/input/lulc/
COPY input/impedance/*.tif /app/input/impedance/ 

# to copy the first script (non-MPI mode) into the container
COPY loop_lulc_mpi.sh /app/loop_lulc_mpi.sh

# to make bash file with commands executable
RUN chmod +x /app/loop_lulc_mpi.sh

# to set the entry point with all commands
ENTRYPOINT ["bash","/app/loop_lulc_mpi.sh"]

