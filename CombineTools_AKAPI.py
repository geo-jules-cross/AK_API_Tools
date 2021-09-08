# -*- coding: utf-8 -*-
#------------------------------------------------------------------------------
# Name:         Import Photo Centers - AK API
#
#   This Python code is used to update geographic metadata (center point and footprint)
#   for scanned aerial film orphan projects as part of the BLM/EROS AK API.
#   Created at the National Operations Center, Bureau of Land Management.
#
# Author:       Jake Slyder, jslyder@blm.gov and Julian Cross, jcross@blm.gov
# Created:      8/11/2020
#------------------------------------------------------------------------------

import arcpy
import os

# Allow overwrite
arcpy.env.overwriteOutput = True

# Variables as parameters for a geoprocessing tool
textFilePath=arcpy.GetParameterAsText(0) # photo centers file from Metashape

APSI_Source=arcpy.GetParameterAsText(1)
SQLstr=arcpy.GetParameterAsText(2)
fgdbTmp=arcpy.GetParameterAsText(3)
fcName=arcpy.GetParameterAsText(4) # "APSI_Footprints_ProjectCode"
obliqueFlag=arcpy.GetParameterAsText(5)
missingFramesFlag=arcpy.GetParameterAsText(6)
fcPolyName=arcpy.GetParameterAsText(7)

#Get the path of the location of the file, so that the tool works if the files are moved.
tbPath = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'Alaska API Tools.tbx')
arcpy.ImportToolbox(tbPath)

#Run the two tools
arcpy.ImportPhotoCenters_AKAPITools(textFilePath, APSI_Source, SQLstr, fgdbTmp, fcName, obliqueFlag, missingFramesFlag)

aprx = arcpy.mp.ArcGISProject("CURRENT")
m = aprx.activeMap
out_fc_lyr = m.listLayers()[0]
ref_lyrx = "Air_Photo_Center.lyrx" 
arcpy.ApplySymbologyFromLayer_management(out_fc_lyr, ref_lyrx)
arcpy.SetParameterAsText(8, out_fc_lyr)

arcpy.GenerateFootprintOfAPSIPhotoCenters_AKAPITools(APSI_Source, SQLstr, fgdbTmp, fcPolyName)

aprx = arcpy.mp.ArcGISProject("CURRENT")
m = aprx.activeMap
out_fc_lyr = m.listLayers()[0]
ref_lyrx = "Air_Photo_Footprints.lyrx" 
arcpy.ApplySymbologyFromLayer_management(out_fc_lyr, ref_lyrx)
arcpy.SetParameterAsText(9, out_fc_lyr)