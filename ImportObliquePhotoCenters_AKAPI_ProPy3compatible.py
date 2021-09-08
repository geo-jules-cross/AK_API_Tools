# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
# Name:         Import Oblique Photo Centers - AK API
#
#   This Python code is used to import photo centers estimated in Metashape
#   for scanned aerial film orphan projects as part of the BLM/EROS AK API.
#   Created at the National Operations Center, Bureau of Land Management.
#
# Author:       Julian Cross, jcross@blm.gov
# Created:      7/28/2020
# ------------------------------------------------------------------------------

import arcpy
import pandas as pd
import os as os
from arcgis.features import GeoAccessor, GeoSeriesAccessor

# Allow overwrite
arcpy.env.overwriteOutput = True

# Variables as parameters for a geoprocessing tool
textFilePath=arcpy.GetParameterAsText(0)  # photo centers file from Metashape

APSI_Source=arcpy.GetParameterAsText(1)
SQLstr=arcpy.GetParameterAsText(2)
fgdbTmp=arcpy.GetParameterAsText(3)
fcName=arcpy.GetParameterAsText(4)  # "APSI_Footprints_ProjectCode"

if len(fcName)>0:
    makePts = True
else:
    makePts = False

# Define the spatial reference and set the workspace
sr = arcpy.SpatialReference(4326)   # WGS 84
arcpy.env.workspace=fgdbTmp

tv = arcpy.MakeTableView_management(APSI_Source, 'APSI_Select', SQLstr)

# Run in IDLE
if len(textFilePath) < 1:
    arcpy.AddMessage('Not initiated from toolbox. Reading scripts default parameters.')
    print('Not initiated from toolbox. Reading scripts default parameters.')
    # Variables (Update with every use when running it using IDLE)

def main():

    # Load exported Metashape photo centers text file to pandas dataframe
    names = ['PhotoID', 'X', 'Y', 'Z', 'X_est', 'Y_est', 'Direction']
    cols = ['PhotoID', 'X_est', 'Y_est', 'Direction']
    msPhotoCenters = pd.read_csv(textFilePath, sep='\t',header=1, 
                                names=names, usecols=cols, dtype={'PhotoID': 'str'})

    # Create a feature class in which to store photo centers
    pntTmp = arcpy.CreateFeatureclass_management(fgdbTmp, 'msPhotoCenters',
                                                  'POINT', '', '', '', sr)

    # Add fields to feature class:
    # Photo ID
    arcpy.AddField_management(pntTmp, 'PhotoID', 'TEXT', field_length=50)
    # Longitude
    arcpy.AddField_management(pntTmp, 'Longitude', 'DOUBLE', field_length=8)
    # Latitude
    arcpy.AddField_management(pntTmp, 'Latitude', 'DOUBLE', field_length=8)
    # Direction
    arcpy.AddField_management(pntTmp, 'Direction', 'Text', field_length=10)

    # Create a cursor to insert lines to data
    with arcpy.da.InsertCursor(pntTmp, ['SHAPE@X','SHAPE@Y',
                                         'PhotoID',
                                         'Longitude',
                                         'Latitude',
                                         'Direction']) \
    as iCursor:
        arcpy.AddMessage('insert cursor created...')
        print('insert cursor created...')

        # Iterate through table and create a point with the Photo ID for each line
        for i in range(len(msPhotoCenters)):
            x = msPhotoCenters.X_est[i]
            y = msPhotoCenters.Y_est[i]
            d = msPhotoCenters.Direction[i]
            iCursor.insertRow((x, y,
                               ('AR' + str(msPhotoCenters.PhotoID[i][0:13]).upper()),
                               x,
                               y,
                               d))
            print('AR' + str(msPhotoCenters.PhotoID[i][0:13]).upper())

        arcpy.AddMessage('insert cursor completed...')
        print('insert cursor completed...')
    del iCursor

    # Set API metadata fields to update
    uFields = ['USGS_ENTITY_ID_NO', 'CENTER_LAT', 'CENTER_LON', 'OBLIQUE_DIR_TXT']
    sFields = ['PhotoID', 'Latitude', 'Longitude', 'Direction']

    # Create a cursor to update metadata with new photo centers
    with arcpy.da.UpdateCursor(tv, uFields) as uCursor:
        arcpy.AddMessage('update cursor created...')
        print('update cursor created...')
        for urow in uCursor:
            with arcpy.da.SearchCursor(pntTmp, sFields) as sCursor:
                for srow in sCursor:
                    if urow[0] == srow[0]:
                        urow[1] = srow[1]
                        urow[2] = srow[2]
                        if (srow[3] is None):
                            continue
                        else:
                            urow[3] = srow[3]
                        uCursor.updateRow(urow)
                        
    arcpy.AddMessage('update cursor completed...')
    print('update cursor completed...')
    del uCursor, sCursor                    

    arcpy.Delete_management(pntTmp)

    if makePts:
        arcpy.XYTableToPoint_management(tv,fcName,'CENTER_LON','CENTER_LAT',"",sr)
        
    LoadLayer()

def LoadLayer():

    try:
        # If user is in ArcGIS Pro
        aprx = arcpy.mp.ArcGISProject("CURRENT")
        m = aprx.activeMap
        m.addDataFromPath(os.path.join(fgdbTmp,fcName))
        ref_lyrx = r"T:\OC\GEOSpSection\NATL\Aerial_Imagery\_gis\APSI\AK\_Updating_API_Table\Air_Photo_Center.lyrx" 
        out_fc_lyr = m.listLayers()[0]
        arcpy.ApplySymbologyFromLayer_management(out_fc_lyr, ref_lyrx)
        arcpy.SetParameterAsText(5, out_fc_lyr)
    except Exception as e:
        arcpy.AddWarning(e)
        arcpy.AddWarning("!New Photo Centers Feature Class could not be added to your current map.")


if __name__ == '__main__':
    main()
