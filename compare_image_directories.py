"""
Created on Thu June 5 2020

    # The first directory should have a larger set of files
    # The second directory is missing files
    # The comparison is to the left

@author: jcross
"""

import os
from os.path import splitext
import sys

if sys.version_info[0] == 2:
    from Tkinter import *
    import tkFileDialog as fdialog
else:
    from tkinter import *
    import tkinter.filedialog as fdialog

# List all files in the directory tree of the given path
def getListOfFiles_FromDir():
    
    root = Tk()
    dirName = fdialog.askdirectory(parent=root, initialdir="/",\
                                  title='Please select an image directory:')
    root.destroy()
    
    os.chdir(dirName)
    
    # Create a list of file and sub directories 
    allFiles = list()
    
    for root, dirs, files in os.walk("."):
        for filename in files:
            allFiles.append(filename.lower())
                
    return allFiles        
 
# Import an Earth Explorer Bulk Download as list
def getListOfFiles_FromTxt():
    
    root = Tk()
    fileName = fdialog.askopenfile(mode ='r',\
                               filetypes =[('Text Files', '*.txt')],\
                               title='Please select .txt list of files:')
    root.destroy()
    
    # Create a list of file and sub directories 
    allFiles = list()
    
    for i in fileName:
        allFiles.append(i[2:].rstrip("\n").lower())
        
    return allFiles

def main():
    
    # Define case
    case = 1
    
    if case < 1:
        # Get the list of all files in directories to difference
        list1 = getListOfFiles_FromDir()
        list2 = getListOfFiles_FromDir()
    else:
        list1 = getListOfFiles_FromTxt()
        list2 = getListOfFiles_FromDir()

    # Create a lookup set of the document names without extensions
    if case < 1:
        documents = set([splitext(filename)[0] for filename in list2])
    else:
        documents = set([splitext(splitext(filename)[0])[0] for filename in list2])

    # Compare each stripped filename in list1 to the list of stripped document filenames
    if case < 1:
        differences = [filename for filename in set(list1) if splitext(filename)[0] not in documents]
    else:
        differences = [filename for filename in set(list1) if filename not in documents]

    print(differences)
    
    # Open README textfile and write to it
    file = open("az66as_batch_crop.bls","w") 
 
    txt = "f:/jcross/az-66-as/rawdata/eros_scans/{0}.tif \"\" \n"
    
    file.write("Input1 Output1 \n")        
    # Loop through each original tiff and write input location
    for t in range(len(differences)):
        file.write(txt.format(differences[t]))
        
    file.close()

if __name__ == '__main__':
    main()