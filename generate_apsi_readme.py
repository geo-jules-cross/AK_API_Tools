# -*- coding: utf-8 -*-
"""
Created on Thu Apr 16 2020

@author: jcross
"""

import os
import sys

if sys.version_info[0] == 2:
    from Tkinter import *
    import tkFileDialog as fdialog
else:
    from tkinter import *
    import tkinter.filedialog as fdialog

# List all files in the directory tree of the given path
def getListOfFiles(dirName):
    
    # Create a list of file and sub directories 
    allFiles = list()
    
    for root, dirs, files in os.walk("."):
        for filename in files:
            allFiles.append(filename)
                
    return allFiles        
 
 
def main():
    
#    dirName = os.getcwd()
    
    root = Tk()
    dirName = fdialog.askdirectory(parent=root, initialdir="/",\
                                  title='Please select a directory to generate a README for:')
    root.destroy()
    
    os.chdir(dirName)
    print (str(dirName))
    
    # Get the list of all files in directory tree at given path
    listOfFiles = getListOfFiles(dirName)
    
    # Initializing search string for original .tif file
    Tiff = 'index.tif'
    Tiff2 = 'index(2).tif'
    notTiff = '.tif.'
    
    # List comprehension to find original .tif file
    # Make lowercase in order to catch file extension variants 
    Tiffs = [i for i in listOfFiles\
             if Tiff in i.lower() and notTiff not in i.lower()\
             or Tiff2 in i.lower() and notTiff not in i.lower()]
    
    # Initializing search string for cpts.tif file
    cptsTiff = 'index_cpts.tif'
    cptsTiff2 = 'index(2)_cpts.tif'
    notCptsTiff = 'index_cpts.tif.'
    
    # List comprehension to find cpts.tif file
    cptsTiffs = [i for i in listOfFiles\
                 if cptsTiff in i.lower() and notCptsTiff not in i.lower()\
                 or cptsTiff2 in i.lower() and notCptsTiff not in i.lower()]
    
    # Initializing search string for cpts.txt file
    cptsTxt = 'index_cpts.txt'
    cptsTxt2 = 'index(2)_cpts.txt'
    
    # List comprehension to find cpts.txt file
    cptsTxts = [i for i in listOfFiles\
                if cptsTxt in i.lower() or cptsTxt2 in i.lower()]
    
    # Initializing search string for rectify.tif file
    rectifyTiff = '_rectify.tif'
    rectifyTiff2 = '_rectify(2).tif'
    notRectifyTiff = '_rectify.tif.'
    notRectifyTiff2 = '_rectify(2).tif.'
    
    # List comprehension to find rectify.tif file
    rectifyTiffs = [i for i in listOfFiles\
                    if rectifyTiff in i.lower() and notRectifyTiff not in i.lower()\
                    or rectifyTiff2 in i.lower() and notRectifyTiff2 not in i.lower()]
    
    # Open README textfile and write to it
    file = open("_README.txt","w") 
 
    file.write("\n")        
    file.write(dirName)     # Project folder path
    file.write("\n\n")
    file.write("Description of digital files on this workspace\n\n")
    file.write("_README.txt - this file\n\n\n")
    
    # Loop through each original tiff and write file descriptions to README
    for t in range(len(Tiffs)):
        file.write(Tiffs[t])
        file.write("  - The orginal scanned map\n\n")
        file.write("	-- Scanner - HPDESIGNJETT2300\n")
        file.write("	-- Format - TIFF\n")
        file.write("	-- Quality - (300 dpi)\n\n")
        file.write(cptsTiffs[t])
        file.write("  - Screen shot of Georeferencing View Link Table\n\n")
        file.write(cptsTxts[t])
        file.write("  - Control Points from the Georeferencing exported Georeferencing Link Table\n\n")
        file.write(rectifyTiffs[t])
        file.write("  - The rectified image using targeted Georeferencing Control Points with a Spatial Reference of GCS_North_American_1983\n\n\n")
        
    file.close()
    
    # Print the files
    for elem in listOfFiles:
        print(elem)
 
    print ("****************")
  
if __name__ == '__main__':
    main()