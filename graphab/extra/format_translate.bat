#GDAL should be installed

@echo on
set "inputFolder=indices"
set "outputFolder=indices_cog"

echo Processing started... > format_translate_log.txt

for %%i in (%inputFolder%\*.tif) do (
    echo Processing file: %%i >> progress_log.txt
    gdal_translate -ot Float32 -of COG -co COMPRESS=LZW "%%i" "%outputFolder%\%%~nxi"
    echo File processed: %%i >> progress_log.txt
)

echo Processing completed. >> progress_log.txt
pause
@echo off