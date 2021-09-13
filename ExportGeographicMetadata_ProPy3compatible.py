# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
# Name:      Export EROS Frame Metadata
#
#    This Python code is used to export photo centers in EROS metadata 
#    for scanned aerial frames so they can be imported to Metashape. 
#    Created at the National Operations Center, Bureau of Land Management.
#
# Author:    Julian Cross, jcross@blm.gov
# Created:   7/9/2020
# ------------------------------------------------------------------------------

import arcpy

# Allow overwrite
arcpy.env.overwriteOutput = True

# Variables as parameters for a geoprocessing tool
shp=arcpy.GetParameterAsText(0)
textFilePath=arcpy.GetParameterAsText(1)
altitudeFlag=arcpy.GetParameterAsText(2)
groundOffset=arcpy.GetParameterAsText(3)
fileExtension=arcpy.GetParameterAsText(4)

# Default value
if len(groundOffset) < 1:
    groundOffset = str('0')

def main():
    
    # Open textfile and write to it
    file = open(textFilePath,"w") 
    
    # Access the spatial reference of the shapefile
    ref = arcpy.Describe(shp).spatialReference
    
    # Write spatial reference as WKT
    arcpy.AddMessage(ref.exportToString())
    file.write('#CoordinateSystem: ')
    file.write(ref.exportToString())
    file.write('\n')
    
    # Write column headers
    hdr_str='#Label	X/Longitude	Y/Latitude	Z/Altitude	X_est	Y_est	Z_est'
    arcpy.AddMessage(hdr_str)
    file.write(hdr_str)
    file.write('\n')
    
    # Fields to be written to textfile      
    fields = ['Photo ID', 'Center L_2', 'Center L_1',
              'Flying Hei', 'Scale', 'Focal Leng']
    
    # Create a search cursor to query shapefile data
    with arcpy.da.SearchCursor(shp, fields) as cursor:
        for row in cursor:
            
            # Estimate z coord or flying height, H (in agl) based on
            # H = S * fl, where: S = scale (:) and fl = focal length (mm)
            s = row[4]
            fl = float(row[5].replace(' mm', ''))
            z_est = (s * fl) * 0.001 # conversion factor mm to m
            h_est = z_est + float(groundOffset)
            #h_est = ((row[3] + float(groundOffset))/3.28) # read h from EROS
            
            # Check for altitude flag and set z value
            z = h_est if (altitudeFlag == 'true') else None

            # For each row write PHOTO_ID and photo center x and y coords
            arcpy.AddMessage(u'{0}{1}, {2}, {3}, {4}'.format(
                    row[0],
                    fileExtension,
                    None if float(row[1])==0 else row[1],
                    None if float(row[2])==0 else row[2],
                    z))    
            file.write(u'{0}{1}\t{2}\t{3}\t{4}'.format(
                    row[0],
                    fileExtension,
                    None if float(row[1])==0 else row[1],
                    None if float(row[2])==0 else row[2],
                    z))
            file.write('\n')
            
if __name__ == '__main__':
    main()