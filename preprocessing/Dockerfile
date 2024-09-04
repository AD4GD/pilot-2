# syntax=docker/dockerfile:1
FROM ghcr.io/osgeo/gdal:ubuntu-small-latest AS base
WORKDIR /app

RUN apt-get update && apt-get install -y \
    python3-pip python3.12-venv nodejs npm

RUN python3 -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
COPY requirements.txt .
RUN pip install -r requirements.txt
RUN npm install -g osmtogeojson

WORKDIR /data
CMD ["jupyter" , "lab", "--allow-root", "--port=9999", "--ip=0.0.0.0", "--no-browser"]