# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
#
#   This Python code combines frames from multiple .TXT files, merging the
#   full list of frames with the list of aligned frames and calculating an
#   average value for required fields.
#
# Author:       Julian Cross, jcross@blm.gov
# Created:      9/14/2021
# -----------------------------------------------------------------------------

import sys
import os
import pandas as pd

if sys.version_info[0] == 2:
    from Tkinter import *
    import tkFileDialog as fdialog
else:
    from tkinter import *
    import tkinter.filedialog as fdialog
    
root = Tk()

cols = ['PhotoID', 'X', 'Y', 'Z', 'X_est', 'Y_est', 'Z_est','H_est','H_g']

allTxtFile = fdialog.askopenfilename(filetypes =[('Text Files', '*.txt')],\
                           title='Please select .txt file with all frames:')

allDF = pd.read_csv(allTxtFile, sep='\t',header=1, 
                    names=cols, dtype={'PhotoID': 'str'})

dirName = fdialog.askdirectory(parent=root, initialdir="/",\
                title='Please select directory with aligned frames .txt file(s):')
root.destroy()

os.chdir(dirName)
    
# Create a list of file and sub directories 
filenames = list()
    
for root, dirs, files in os.walk("."):
    for filename in files:
        filenames.append(filename.lower())

root = Tk()

# concatanate multiple files
dataframes = []

# Iterate through list
for file in filenames:

    dataframes.append(pd.read_csv(file, sep='\t',header=1, 
                    names=cols, dtype={'PhotoID': 'str'}))

alignedDF = pd.concat(dataframes, axis=0)

allDF['PhotoID'] = allDF['PhotoID'].str[2:]
allDF['PhotoID'] = allDF['PhotoID'].str.lower()

allDF.set_index('PhotoID', inplace = True)
alignedDF.set_index('PhotoID', inplace = True)
allDF.update(alignedDF)

allDF.fillna(allDF.mean(), inplace=True)

allDF['X'] = allDF['X'].map(lambda x: '{0:.3f}'.format(x))
allDF['Y'] = allDF['Y'].map(lambda x: '{0:.3f}'.format(x)) 
allDF['Z'] = allDF['Z'].map(lambda x: '{0:.3f}'.format(x))
allDF['Z_est'] = allDF['Z_est'].map(lambda x: '{0:.3f}'.format(x))
allDF['H_est'] = allDF['H_est'].map(lambda x: '{0:.3f}'.format(x)) 
allDF['H_g'] = allDF['H_g'].map(lambda x: '{0:.3f}'.format(x))

# create text file and write to it
newTxtFile = fdialog.asksaveasfilename(filetypes =[('Text Files', '*.txt')],\
                           title='Choose write location:')

with open(newTxtFile, "w", newline="") as file:

    # write spatial reference as WKT
    file.write('#CoordinateSystem: WGS84; EPSG: 4326')
    file.write('\n')
    
    # Write column headers
    header_str='#Label\tX\tY\tZ\tX_est\tY_est\tZ_est\tH_est\tH_ground'
    file.write(header_str)
    file.write('\n')
    
    file.close()
    
allDF.to_csv(newTxtFile, header=None, sep="\t", float_format='%11.6f', mode = "a")

print("Script finished!")

root.destroy()