# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
# Name:         Import Photo Centers - AK API
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
obliqueFlag=arcpy.GetParameterAsText(5)
scaleFlag=arcpy.GetParameterAsText(6)
missingFramesFlag=arcpy.GetParameterAsText(7)

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

    if (obliqueFlag == 'true'):
        importOblique()
    else:
        importVertical()

    if makePts:
        arcpy.XYTableToPoint_management(tv,fcName,'CENTER_LON','CENTER_LAT',"",sr)
        
    LoadLayer()

def importVertical():
    # Load exported Metashape photo centers text file to pandas dataframe
    names = ['PhotoID', 'X', 'Y', 'Z', 'X_est', 'Y_est', 'Z_est','H_est','H_g']
    cols = ['PhotoID', 'X_est', 'Y_est', 'Z_est', 'H_est']
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
    # Altitude
    arcpy.AddField_management(pntTmp, 'Altitude', 'FLOAT', field_length=8,
                              field_precision=6, field_scale=2,
                              field_is_nullable=True)
    # Photo Height
    arcpy.AddField_management(pntTmp, 'PhotoHeight', 'FLOAT', field_length=8,
                              field_precision=6, field_scale=2,
                              field_is_nullable=True)

    # Create a cursor to insert lines to data
    with arcpy.da.InsertCursor(pntTmp, ['SHAPE@X','SHAPE@Y',
                                         'PhotoID',
                                         'Longitude',
                                         'Latitude',
                                         'Altitude',
                                         'PhotoHeight']) \
    as iCursor:
        arcpy.AddMessage('insert cursor created...')
        print('insert cursor created...')

        # list to store frames without alignment
        missing = []

        # Iterate through table and create a point with the Photo ID for each line
        for i in range(len(msPhotoCenters)):
            x = msPhotoCenters.X_est[i]
            y = msPhotoCenters.Y_est[i]
            h = msPhotoCenters.H_est[i]
            if [j for j in (x, y) if pd.isnull(j) == False]:
                if pd.isnull(msPhotoCenters.Z_est[i]) == False:
                    z = msPhotoCenters.Z_est[i]
                else:
                    z = 0
                iCursor.insertRow((x, y,
                                   ('AR' + str(msPhotoCenters.PhotoID[i][0:13]).upper()),
                                   x,
                                   y,
                                   z,
                                   h))
                print('AR' + str(msPhotoCenters.PhotoID[i][0:13]).upper())
                arcpy.AddMessage(('AR' + str(msPhotoCenters.PhotoID[i][0:13]).upper()))
            else:
                # Add Photo ID to missing list
                missing = missing + ['AR' + str(msPhotoCenters.PhotoID[i][0:-4])]
                arcpy.AddMessage('missing x, y, or z values for:')
                print('missing x, y, or z values for:')
                arcpy.AddMessage('AR' + str(msPhotoCenters.PhotoID[i][0:-4]))
                print('AR' + str(msPhotoCenters.PhotoID[i][0:-4]))

        arcpy.AddMessage('insert cursor completed...')
        print('insert cursor completed...')
    del iCursor

    # Check missing frames flag
    if (missingFramesFlag == 'true'):
        arcpy.AddMessage('estimating missing photo centers...')
        print('estimating missing photo centers...')
        pntTmp = EstimateMissingPC(pntTmp, tv, missing)

    # Set API metadata fields to update
    uFields = ['USGS_ENTITY_ID_NO', 'CENTER_LAT', 'CENTER_LON',
               'PHOTO_SCALE_QTY', 'LENS_FOCAL_LENGTH_QTY']
    sFields = ['PhotoID', 'Latitude', 'Longitude', 'PhotoHeight']

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
                        # Check if project scale (S) is missing and estimate
                        # S = fl/pH: focal length (fl) and photo height (pH)
                        # display scale as denominator e.g. 1:20000 = 20000
                        if scaleFlag == 'false':
                            urow[3] = urow[3]
                        elif(urow[3] is None or urow[3] == 0):
                            arcpy.AddMessage('estimating scale...')
                            print('estimating scale...')
                            urow[3] = int((srow[3]*39.36)/float(urow[4]))
                            arcpy.AddMessage(int((srow[3]*39.36)/float(urow[4])))
                        else:
                            urow[3] = urow[3]
                        uCursor.updateRow(urow)
                        
    arcpy.AddMessage('update cursor completed...')
    print('update cursor completed...')
    del uCursor, sCursor

    arcpy.Delete_management(pntTmp)

def importOblique():
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
            arcpy.AddMessage(('AR' + str(msPhotoCenters.PhotoID[i][0:13]).upper()))

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

# Function to compute coordinates x4,y4 along the prolongation of
# the line from x1,y1 to x2,y2 where p1, p2, p3 are equally spaced
def CalcEndpoint(x1,y1,z1,h1,x2,y2,z2,h2):
    dx = x2 - x1
    dy = y2 - y1
    dz = z2 - z1
    dh = h2 - h1
    x4 = x2 + dx
    y4 = y2 + dy
    z4 = z2 + dz
    h4 = h2 + dz
    return (x4, y4, z4, h4)

# Function to compute coordinates x4,y4 at the mid-point
# along the the line from x2,y2 to x3,y3
def CalcMidpoint(x2,y2,z2,h2,x3,y3,z3,h3):
    x4 = (x3 + x2)/2
    y4 = (y3 + y2)/2
    z4 = (z3 + z2)/2
    h4 = (h3 + h2)/2
    return (x4, y4, z4, h4)

# Function to estimate photo centers for missing frames
def EstimateMissingPC(pntTmp, tv, missing):


    apiFields = ['USGS_ENTITY_ID_NO', 'ROLL_NO',
                 'FLIGHT_LINE_NO', 'PHOTO_FRAME_NO']

    # create a Spatially Enabled DataFrame (pandas DF) object
    sdf = pd.DataFrame.spatial.from_table(tv, fields=apiFields)

    # Loop through missing cameras
    for camera in missing:

        #arcpy.AddMessage(camera)
    
        # Find flight line
        if sdf.ROLL_NO[sdf.USGS_ENTITY_ID_NO == camera].empty:
            continue
        else:
            roll = sdf.ROLL_NO[sdf.USGS_ENTITY_ID_NO == camera].iloc[0]
            strip = sdf.FLIGHT_LINE_NO[sdf.USGS_ENTITY_ID_NO == camera].iloc[0]
            frame = sdf.PHOTO_FRAME_NO[sdf.USGS_ENTITY_ID_NO == camera].iloc[0]
    
            flightline = sdf[(sdf.ROLL_NO == roll) & (sdf.FLIGHT_LINE_NO == strip)]
    
            # Check if this frame in the first or last end-point or mid-point
            if (frame == flightline.PHOTO_FRAME_NO.max()):
                arcpy.AddMessage('this frame is the last end-point...')
                case = 2
                # Find neighboring points on flight line data series
                n1 = flightline.USGS_ENTITY_ID_NO[flightline.PHOTO_FRAME_NO == frame - 2].iloc[0]
                n2 = flightline.USGS_ENTITY_ID_NO[flightline.PHOTO_FRAME_NO == frame - 1].iloc[0]
            elif (frame == flightline.PHOTO_FRAME_NO.min()):
                arcpy.AddMessage('this frame is the first end-point...')
                case = 1
                # Find neighboring points on flight line data series
                n1 = flightline.USGS_ENTITY_ID_NO[flightline.PHOTO_FRAME_NO == frame + 2].iloc[0]
                n2 = flightline.USGS_ENTITY_ID_NO[flightline.PHOTO_FRAME_NO == frame + 1].iloc[0]
            else:
                arcpy.AddMessage('this frame is a mid-point...')
                case = 0
                # Find neighboring points on flight line data series
                n2 = flightline.USGS_ENTITY_ID_NO[flightline.PHOTO_FRAME_NO == frame + 1].iloc[0]
                n3 = flightline.USGS_ENTITY_ID_NO[flightline.PHOTO_FRAME_NO == frame - 1].iloc[0]
            #arcpy.AddMessage(case)
    
            # Check case
            if (case == 1) or (case == 2):
                # Start cursor and find x and y coordinates of neighbors
                with arcpy.da.SearchCursor(pntTmp,['PhotoID',
                                                   'SHAPE@X','SHAPE@Y',
                                                   'Altitude','PhotoHeight'])\
                as sCursor:
                    for row in sCursor:
                        if (row[0] == n1):
                            x1 = row[1]
                            y1 = row[2]
                            z1 = row[3]
                            h1 = row[4]
                        if (row[0] == n2):
                            x2 = row[1]
                            y2 = row[2]
                            z2 = row[3]
                            h2 = row[4]
                # Do geometry calculation
                coords = (x1,y1,z1,h1,x2,y2,z2,h2)
                estCoords = CalcEndpoint(*coords)
                
            # Check case
            elif (case == 0):
                # Start cursor and find x and y coordinates of neighbors
                with arcpy.da.SearchCursor(pntTmp,['PhotoID',
                                                   'SHAPE@X','SHAPE@Y',
                                                   'Altitude','PhotoHeight'])\
                as sCursor:
                    for row in sCursor:
                        if (row[0] == n2):
                            x2 = row[1]
                            y2 = row[2]
                            z2 = row[3]
                            h2 = row[4]
                        if (row[0] == n3):
                            x3 = row[1]
                            y3 = row[2]
                            z3 = row[3]
                            h3 = row[4]
                # Do geometry calculation
                coords = (x2,y2,z2,h2,x3,y3,z3,h3)
                estCoords = CalcMidpoint(*coords)
    
            # Create a cursor to add new photo centers
            with arcpy.da.InsertCursor(pntTmp, ['SHAPE@X','SHAPE@Y',
                                             'PhotoID',
                                             'Longitude',
                                             'Latitude',
                                             'Altitude',
                                             'PhotoHeight'])\
            as eCursor:
                arcpy.AddMessage('estimate cursor created...')
                eCursor.insertRow((estCoords[0], estCoords[1], # geom
                                   camera,          # photo ID
                                   estCoords[0],    # longitude
                                   estCoords[1],    # latitude
                                   estCoords[2],    # altitude
                                   estCoords[3]))             # photo height
    
            arcpy.AddMessage('estimate cursor completed...')
            del sCursor, eCursor

    return pntTmp


def LoadLayer():

    try:
        # If user is in ArcGIS Pro
        aprx = arcpy.mp.ArcGISProject("CURRENT")
        m = aprx.activeMap
        m.addDataFromPath(os.path.join(fgdbTmp,fcName))
        ref_lyrx = "Air_Photo_Center.lyrx" 
        out_fc_lyr = m.listLayers()[0]
        arcpy.ApplySymbologyFromLayer_management(out_fc_lyr, ref_lyrx)
        arcpy.SetParameterAsText(8, out_fc_lyr)
    except Exception as e:
        arcpy.AddWarning(e)
        arcpy.AddWarning("!New Photo Centers Feature Class could not be added to your current map.")


if __name__ == '__main__':
    main()
