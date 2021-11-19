# -*- coding: utf-8 -*-
#------------------------------------------------------------------------------
# Name:         Export Photo Centers w/ Photo Height
#
#   This Python code is used to export photo centers estimated in Metashape
#   with photo height (h) above ground level (AGL), rather than default export
#   of camera altitude above mean sea-level (MSL) for scanned aerial film 
#   orphan projects as part of the BLM/EROS AK API. 
#   Created at the National Operations Center, Bureau of Land Management.
#
#   Some of the Python API code for add_altitude() function is derived from:
#   'add_altitude_to_reference.py' (github.com/agisoft-llc/metashape-scripts)
#
# Author(s):    Julian Cross, jcross@blm.gov and Jake Slyder jslyder@blm.gov
# Created:      7/29/2020
#------------------------------------------------------------------------------

import Metashape
import math

# Checking compatibility
comp_version = "1.7"
version = ".".join(Metashape.app.version.split('.')[:2])
if version != comp_version:
    message = 'Incompatible MS version:{} != {}'.format(version,comp_version)
    raise Exception(message)

def export_camera_height():
#    Export flying/photo height (h) above ground level for each camera

    doc = Metashape.app.document
    if not len(doc.chunks):
        raise Exception("No chunks!")
    chunk = doc.chunk
    # access the chunk spatial reference as WKT string
    ref_wkt = chunk.crs.wkt2
    
#    if chunk.model:
#        print(True)
#        surface = chunk.model
#        print(surface)
#    elif chunk.dense_cloud:
#        print(True)
#        surface = chunk.dense_cloud
#        print(surface)
#    elif chunk.elevation:
#        print(True)
#        surface = chunk.elevation
#        print(surface)
#    else:
    
    surface = chunk.point_cloud
    print(surface)

    textFilePath = Metashape.app.getSaveFileName("Specify export text file:")

    print("Script started...")

    # initiate lists to store labels and coordinates
    labels = []
    # estimated values of X,Y,Z
    e_x_list = []; e_y_list = []; e_z_list = []
    # source (measured) values of X,Y,Z
    s_x_list = []; s_y_list = []; s_z_list = []
    # estimated camera height (AGL) h
    e_h_list = []; g_h_list = []
    
    for camera in chunk.cameras:
        
            sensor = camera.sensor
            T = chunk.transform.matrix
            
            if camera.transform:  # just for the aligned cameras
                labels.append(camera.label)
                print(camera.label)
    
                # estimated values of X,Y,Z
                estimated = chunk.crs.project(T.mulp(camera.center))
                e_x_list.append(estimated.x)
                e_y_list.append(estimated.y)
                e_z_list.append(estimated.z)
                
                # use pick point to find ground height
                origin = camera.center
                if sensor.film_camera:
                    coords = [int(camera.photo.meta['File/ImageWidth'])/2, 
                              int(camera.photo.meta['File/ImageWidth'])/2]
                    target = camera.unproject(Metashape.Vector(coords))
                    
                else:
                    coords = [int(sensor.width)/2, int(sensor.height)/2]
                    target = camera.transform.mulp(
                                sensor.calibration.unproject(
                                    Metashape.Vector(coords)))
                
                point = surface.pickPoint(origin, target)
                ground_h = chunk.crs.project(T.mulp(point))
                h = estimated.z - ground_h.z
                e_h_list.append(h)
                g_h_list.append(ground_h.z)
                
            else:
                labels.append(camera.label)
                print(camera.label)
                
                e_x_list.append(math.nan)
                e_y_list.append(math.nan)
                e_z_list.append(math.nan)
                e_h_list.append(math.nan)
                g_h_list.append(math.nan)
            
            if camera.reference.location: # just cameras with source location
                # source (measured) values of X,Y,Z
                source = camera.reference.location
                s_x_list.append(source.x)
                s_y_list.append(source.y)
                s_z_list.append(source.z)
            else:
                s_x_list.append(math.nan)
                s_y_list.append(math.nan)
                s_z_list.append(math.nan)
            
            # List of coordinate lists for export
            lists = [labels,
            s_x_list, s_y_list, s_z_list,
            e_x_list, e_y_list, e_z_list, 
            e_h_list,  g_h_list]


    # create text file and write to it
    with open(textFilePath, "w", newline="") as file:
    
        # write spatial reference as WKT
        file.write('#CoordinateSystem: ')
        file.write(ref_wkt)
        file.write('\n')
        
        # Write column headers
        header_str='#Label\tX\tY\tZ\tX_est\tY_est\tZ_est\tH_est\tH_ground'
        file.write(header_str)
        file.write('\n')
        
        for row in zip(*lists):
            file.write('{0}\t'.format(row[0])) # label
            file.write('{0:.6f}\t{1:.6f}\t{2:.3f}\t{3:.6f}\t'.format(
                    row[1], row[2], row[3], row[4]))
            file.write('{0:.6f}\t{1:.3f}\t{2:.3f}\t{3:.3f}\n'.format(
                    row[5], row[6], row[7], row[8]))

    print("Script finished!")

#export_camera_height()

label = "BLM NOC Tools/Export photo height above ground level (AGL)"
Metashape.app.addMenuItem(label, export_camera_height)
