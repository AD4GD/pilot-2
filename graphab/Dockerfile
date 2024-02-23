# syntax=docker/dockerfile:1
FROM amazoncorretto:latest as base
WORKDIR /app

COPY graphab-2.8.6.jar graphab-2.8.6.jar 

# to create folders with input data
RUN mkdir /input/lulc/ && \
    mkdir /input/impedance/ 

# to copy the content of folders with input data
COPY input/lulc/*.tif /input/lulc/
COPY input/impedance/*.tif /input/impedance/ 

# to copy the first script (non-MPI mode) into the container
COPY entrypoint.sh /app/entrypoint.sh

# to make bash file with commands executable
RUN chmod +x /app/entrypoint.sh

# to set the entry point with all commands
ENTRYPOINT ["/app/entrypoint.sh"]

