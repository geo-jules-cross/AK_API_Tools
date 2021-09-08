''' 2014: This Python code is used to compute the coordinates of 4 corners of a photo
    based on known photo center in the APSI project.
    Implemented by Ernie JK Liu in 2014 at the National Operations Center, Bureau of Land Management.'''

''' 2019: Updates to the code were made by Jennifer McCollom (ifer) in November 2019
    to include compatibility with both ArcGIS Desktop & ArcGIS Pro (py 2.7 & 3.x).
    The script can be set up as a Toolbox tool in both Desktop & Pro or run stand alone.
    Additional updates included:
        -Working directly with an SDE connection to the APSI photo corner dataset to make a selection based on the PROJECT_CODE field.
        -Creation of an interim feature class inside of a scratch file geodatabase (instead of starting with a shapefile).
        -Creation of a polygon feature class (footprints) with complete attributes to illustrate the extent of the photo corners.'''
''' 2020: 02 Adjusted the field values based on new APSI schema'''
''' ##### From Ernie: Remarked as those parts need to be modified based on different attributes
           of photo centers dataset.'''

import os, sys
import arcpy
import math
import arcpy.da as da
from arcpy import env
from operator import itemgetter
from collections import Counter

arcpy.env.overwriteOutput = True

# Variables as parameters (For use when creating a ArcGIS Toolbox. Comment out the Variables code above & use this code to make a py script tool.)
APSI_Source = ''
APSI_Source=arcpy.GetParameterAsText(0) #parameter type: Feature Class w\ default sde feature class in field. Must have access to the sde connect file.
SQLstr=arcpy.GetParameterAsText(1) #parameter type: SQL Expression w\ Obtain From pointing to first argument
fgdbTmp=arcpy.GetParameterAsText(2) #parameter type: Workspace or Feature Dataset
footprntfn=arcpy.GetParameterAsText(3) #parameter type: string w\default as "APSI_Footprints_ProjectCode"
standalone="N"
if len(footprntfn)>0:
    makePolys = True
else:
    makePolys = False
spatialRef = arcpy.SpatialReference(4326)   #WGS 84
#spatialRef = arcpy.SpatialReference(4269)  #NAD 83

#if len(APSI_Source) < 1:
#    # Variables (Update with every use when running it using IDLE)
#    APSI_Source=r"D:\AlaskaAPI\API.gdb\Air_Photo_Metadata_JSWorking"
#    SQLstr="FLIGHT_LINE_NAME = 'Chelatna Lake'"
#    fgdbTmp=r"D:\AlaskaAPI\Testing\Default.gdb"
#    footprntfn="Chelatna_Lake_Footprints"
#    standalone="Y"

#General variables needed
#GCS_NAD83specs = "GEOGCS['GCS_North_American_1983',DATUM['D_North_American_1983',SPHEROID['GRS_1980',6378137.0,298.257222101]],PRIMEM['Greenwich',0.0],UNIT['Degree',0.0174532925199433]];-399.999999994899 -399.999999996862 558864763.32536;-100000 10000;-100000 10000;2.86294664648326E-08;0.001;0.001;IsHighPrecision"

#Create fc to be used in main function
env.workspace=fgdbTmp
fc="APSIselect"
outfc="APSIselect_corners"
print(APSI_Source)
if arcpy.Exists(APSI_Source):
    print("Table exists!")
else:
    print("Table doesn't exist")
arcpy.MakeTableView_management(APSI_Source, "tmpfeatures", SQLstr)
#arcpy.CopyRows_management("tmpfeatures", fc)
arcpy.XYTableToPoint_management("tmpfeatures", fc, "CENTER_LON", "CENTER_LAT", "", spatialRef)

print('Created a temporary table based on the SQL statement.')
arcpy.AddMessage('Created a temporary table based on the SQL statement.')

def main():
    addfieldslst=["UR_LON","UR_LAT","UL_LON","UL_LAT","LL_LON","LL_LAT","LR_LON","LR_LAT"]
    arcpy.DeleteField_management(fc,addfieldslst)
    for fld in addfieldslst:
        arcpy.AddField_management(fc, fld, "DOUBLE", "", "", 15)

    # Get all fields in shape file
    rows = arcpy.SearchCursor(fc)
    # Create a list of string fields
    fields_fc = arcpy.ListFields(fc)
    fields=[]
    for field in fields_fc:
        if field.type != "Geometry":
            fields.append(field.name)

    #print(fields)
    for i in range(len(fields)):
        print(i,fields[i])
    #arcpy.AddMessage(fields)
    len_fld=len(fields)
    print (" No. of fields in photo center: %s" %len_fld)
    arcpy.AddMessage(" No. of fields in photo center: %s" %len_fld)

    # Get all records in shape file
    records=[]
    for row in rows:
        value=[]
        for field in fields_fc:
            if field.type != "Geometry":
                value.append(row.getValue(field.name))
        records.append(value)

    length=len(records)
    arcpy.AddMessage(fields)
    with arcpy.da.UpdateCursor(fc,fields) as cursor:
        prj_name=[]
        st_records=sorted(records, key=itemgetter(13,12,65))##### Flight line name, Flight Line No, and Frame_Num
        #arcpy.AddMessage("st_records")
        #arcpy.AddMessage(st_records)
        row=0
        while row < length:
            prj_name.append(st_records[row][13]) #####changed
            row +=1
        #arcpy.AddMessage('prj_name')
        #arcpy.AddMessage(prj_name)
        # Filter out un-repeated project name
        #prj_list=(Counter(prj_name)).keys()###dropped due to 2.7t3 code
        prj_list = list(Counter(prj_name)) ###changed due to 2.7 to 3 code, but works with both
        prj_count=(Counter(prj_name)).values()
        prj_length=len(prj_list)
        print (' Number of projects: %s' %prj_length)
        arcpy.AddMessage(' Number of projects: %s' %prj_length)
        i=0
        j=0
        prj_group=[]
        for i in range(0, prj_length):
            prj_group.append([])
            for j in range(0, length):
                #arcpy.AddMessage("Left: %s"%records[j][13])
                #arcpy.AddMessage("Right: %s \n\n\n"%prj_list[i])
                if (records[j][13]==prj_list[i]): #####changed
                    prj_group[i].append(records[j])
                j +=1
            i +=1

        #print("project groups", prj_group)

        i=0
        prj_roll=[] # roll number for each prj
        prj_flight=[] # flight number for each prj

        fld_row0=[]
        fld_row1=[]
        fld_row2=[]
        fld_photo=[]

        coord_pt0=[]
        coord_pt1=[]
        coord_pt2=[]
        corner_pt1=[]
        corner_pt2=[]
        #arcpy.AddMessage("prj_length")
        #arcpy.AddMessage(prj_length)

        for i in range (0, prj_length):
            arcpy.AddMessage("Iterating through projects to get roll and flight count")

            count1=len(prj_group[i]) # no. of points for each prj
            #arcpy.AddMessage('count1')
            #arcpy.AddMessage(count1)
            #arcpy.AddMessage(prj_group[i])
            #print (' Project name: %s' %prj_group[i][0][1]) #####changed
            #arcpy.AddMessage("prj_group[i]")
            #arcpy.AddMessage(prj_group[i])
            #arcpy.AddMessage(' Project name: %s' %prj_group[i][0][13])
            # Filter out un-repeated roll/flight number
            prj_roll.append([])
            prj_flight.append([])
            for j in range(0,count1):
                #arcpy.AddMessage("prj_group[i][j]")
                #arcpy.AddMessage(prj_group[i][j])
                prj_roll[i].append(prj_group[i][j][29]) #####changed
                prj_flight[i].append(prj_group[i][j][12]) #####changed
                j +=1
            count_roll=len(Counter(prj_roll[i])) # total roll number for each prj
            count_flight=len(Counter(prj_flight[i])) # total flight number for each prj

            # Multi rolls, multi flight lines
            if count_roll > 1:
                # print (' Roll number: %s' %count_roll)
                value_roll=Counter(prj_roll[i]).values()
                # print (' Values of roll: %s' %value_roll)
                #key_roll=Counter(prj_roll[i]).keys() ###dropped due to 2.7t3 code
                key_roll=list(Counter(prj_roll[i])) ###changed due to 2.7 to 3 code, but works with both
                # print (' Keys of roll: %s' %key_roll)
                prj_newgroup1=[]
                prj_flight1=[]
                for mi in range(count_roll):
                    prj_newgroup1.append([])
                    for mj in range(count1):
                        if prj_group[i][mj][29]==key_roll[mi]: #####changed ##JC Changed from 3 to 29
                            prj_newgroup1[mi].append(prj_group[i][mj])
                    #print prj_newgroup1[mi][1]
                    count2=len(prj_newgroup1[mi])
                    prj_flight1.append([])
                    for j in range(0,count2):
                        prj_flight1[mi].append(prj_newgroup1[mi][j][12]) #####changed ##JC Changed from 4 to 12
                        j +=1
                    count_flight1=len(Counter(prj_flight1[mi])) # total flight number for each prj
                    #print(' Count flight: %s' %count_flight1)

                    #value_flight1=Counter(prj_flight1[mi]).values() ###dropped due to 2.7t3 code
                    value_flight1=list(Counter(prj_flight1[mi]).values()) ###changed due to 2.7 to 3 code, but works with both
                    #print value_flight
                    #key_flight1=Counter(prj_flight1[mi]).keys() ###dropped due to 2.7t3 code
                    key_flight1=list(Counter(prj_flight1[mi])) ###changed due to 2.7 to 3 code, but works with both
                    #print key_flight
                    row0=[]
                    pt0=[]
                    prj_newgroup2=[]
                    for iii in range(count_flight1):
                        prj_newgroup2.append([])
                        for jjj in range(count2):
                            # print key_flight1[iii]
                            if prj_newgroup1[mi][jjj][12]==key_flight1[iii]: #####changed  ##JS Changed from 4 to 12
                                prj_newgroup2[iii].append(prj_newgroup1[mi][jjj])
                        print("value flight iii",value_flight1[iii])
                        arcpy.AddMessage("Test3")
                        [row0, pt0]=corner_photo(prj_newgroup2[iii], value_flight1[iii], len_fld) # cursor

                        fld_photo=fld_photo+row0
                        print('fld_photo',fld_photo)
                        coord_pt0=coord_pt0+pt0
                        print('coord_pt0',coord_pt0)

            # Single roll, multi flight lines
            row1=[]
            pt1=[]
            if ((count_roll== 1) and (count_flight > 1)):

                #value_flight=Counter(prj_flight[i]).values() ###dropped due to 2.7t3 code
                value_flight=list(Counter(prj_flight[i]).values()) ###changed due to 2.7 to 3 code, but works with both
                #arcpy.AddMessage("value_flight: %s"%value_flight)
                #key_flight=Counter(prj_flight[i]).keys() ###dropped due to 2.7t3 code
                key_flight=list(Counter(prj_flight[i])) ###changed due to 2.7 to 3 code, but works with both
                #arcpy.AddMessage("key_flight: %s"%key_flight)
                prj_newgroup=[]
                #arcpy.AddMessage("count flight: %s"%count_flight)
                for ii in range(count_flight):
                    prj_newgroup.append([])
                    for jj in range(count1):
                        # print key_flight[ii]
                        #arcpy.AddMessage("prj_group[i][jj]: %s"%prj_group[i][jj])
                        #arcpy.AddMessage("key_flight[ii]: %s"%key_flight[ii])
                        if prj_group[i][jj][12]==key_flight[ii]: #####changed  ##JS Changed from 4 to 12
                            prj_newgroup[ii].append(prj_group[i][jj])
                    #arcpy.AddMessage("Test2")
                    #arcpy.AddMessage("prj_newgroup")
                    #arcpy.AddMessage(prj_newgroup)
                    [row1, pt1]=corner_photo(prj_newgroup[ii], value_flight[ii], len_fld) # cursor

                    fld_photo=fld_photo+row1
                    print('fld_photo',fld_photo)
                    coord_pt1=coord_pt1+pt1
                    print('coord_pt1',coord_pt1)

            # Single roll, single flight line
            row2=[]
            pt2=[]
            arcpy.AddMessage("Count roll: %s"%count_roll)
            arcpy.AddMessage("Count flight: %s"%count_flight)
            if ((count_roll== 1) and (count_flight== 1)):
                #print (' Count roll: %s' %count_roll)
                #print("prj group", prj_group[i])
                #print("count1",count1)
                #print("len fld", len_fld)
                arcpy.AddMessage("Test1")
                [row2, pt2]=corner_photo(prj_group[i], count1, len_fld) # cursor
                print(row2, pt2)

            fld_photo=fld_photo+row2
            coord_pt2=coord_pt2+pt2
            #print('fld_photo',fld_photo)

            #print('coord_pt2',coord_pt2)
        #arcpy.AddMessage("fld_photo")
        #arcpy.AddMessage(fld_photo)
        i=0
        for row in cursor:
            #print(row)
            cursor.updateRow(fld_photo[i])
            i +=1

        coord_photo=coord_pt0+coord_pt1+coord_pt2

        print (' Processed Coord Photo...')
        arcpy.AddMessage(' Processed Coord Photo...')
        # Add points into a shapefile
        pt = arcpy.Point()
        ptGeoms = []
        for p in coord_photo:
            pt.X = p[0]
            pt.Y = p[1]
            ptGeoms.append(arcpy.PointGeometry(pt))
        print (' Processed Point geometry...')
        arcpy.AddMessage(' Processed Point geometry...')

        arcpy.CopyFeatures_management(ptGeoms, outfc)
        arcpy.DefineProjection_management(outfc, spatialRef)
        #arcpy.AddField_management(fc, 'LONGITUDE', "DOUBLE", "", "", 15)  #JS
        #arcpy.AddField_management(fc, 'LATITUDE', "DOUBLE", "", "", 15)   #JS

        #fieldlist=['LONGITUDE','LATITUDE']
        #tokens=['SHAPE@X','SHAPE@Y']
        #with arcpy.da.UpdateCursor(fc,fieldlist+tokens) as cursor:
        #    for row in cursor:
        #        row[2]=row[0]
        #        row[3]=row[1]
        #        cursor.updateRow(row)

    if cursor:
        del cursor

    #Instead of just creating a new feature class, update the input table.
    cursorFieldList =["VENDOR_ID","UR_LON","UR_LAT","UL_LON","UL_LAT","LL_LON","LL_LAT","LR_LON","LR_LAT"]
    with arcpy.da.UpdateCursor(APSI_Source,cursorFieldList,SQLstr) as uCursor:
        for urow in uCursor:
            with arcpy.da.SearchCursor(fc,cursorFieldList) as sCursor:
                for srow in sCursor:
                    if urow[0] == srow[0]:
                        for i in range(1,9):
                            urow[i] = srow[i]
                        uCursor.updateRow(urow)

def corner_photo(prj_photo, nm, len_fields):
    arcpy.AddMessage("corner photo input params:\n %s, %s, %s"%(prj_photo, nm, len_fields))
    # converted exposure number into integer for sorting
#    for mm in range(nm):
        # Dealing with exposure no. has a character (not integer) or having a special character
        #print(prj_photo[mm][65])
#        exp_no=prj_photo[mm][65]
#        print(type(exp_no))
#        len_expno=len(str(exp_no))
#        #split_expno=[exp_no[i:i+1] for i in range(0, len_expno, 1)]
#        new_expno=str(exp_no)
#        if (split_expno[len_expno-1])=='A' or (split_expno[len_expno-1])=='N':
#            if len_expno > 1:
#                for ll in range(len_expno-1):
#                    new_expno=new_expno+split_expno[ll]
#                    # print new_expno
#            else:
#                new_expno=0
#        elif (split_expno[len_expno-1])=='B':
#            if len_expno > 1:
#                for ll in range(len_expno-1):
#                    new_expno=new_expno+split_expno[ll]
#                    # print new_expno
#            else:
#                new_expno=-1
#        elif (split_expno[len_expno-1])=='-':# typo?
#            new_expno=10
#        else:
#            for ll in range(len_expno):
#                new_expno=new_expno+split_expno[ll]
#                #print new_expno
#        prj_photo[mm][5]=int(new_expno) #####changed

    coord_pt=[]
    #arcpy.AddMessage("prj_photo")
    #arcpy.AddMessage(prj_photo)
    #arcpy.AddMessage(prj_photo[0][64])
    #arcpy.AddMessage(prj_photo[0][65])
    #arcpy.AddMessage(prj_photo[0][66])
    sorted_rds=sorted(prj_photo, key=itemgetter(57)) #####changed
    arcpy.AddMessage("prj_photo")
    arcpy.AddMessage(prj_photo)
    i=0
    row_new=[]
    for i in range(0,nm):
        arcpy.AddMessage("prj_photo[i]")
        arcpy.AddMessage(prj_photo[i])
        obj_id0=prj_photo[i][0]
        if nm==1:
            theta=0 # Flight direction for "one point only" flight
            # print (' Only one photo in this project.')
        x01=math.radians(sorted_rds[0][52]) #####changed
        y01=math.radians(sorted_rds[0][51]) #####changed


        exp_num1=sorted_rds[i][57] #####changed  js
        scale=sorted_rds[i][20] #####changed      js
        # Dealing with 9" by 9" photos
        width_photo=(9*2.54*scale)/100.0
        x1=math.radians(sorted_rds[i][52]) #####changed
        y1=math.radians(sorted_rds[i][51]) #####changed

        # converted the arc length located on the assigned latitude
        arc_lat=111132.92-559.82*math.cos(2*y1)+1.175*math.cos(4*y1)
        rad_photo=math.radians((width_photo/arc_lat)/2.0) # half of photo width
        rad_photoS=math.sqrt(2)*rad_photo # slant of (photo width/2)
        if i < nm-1:
            #arcpy.AddMessage("IF statment true!!!!")
            x02=math.radians(sorted_rds[1][52]) #####changed
            y02=math.radians(sorted_rds[1][51]) #####changed
            theta0=math.atan2(y01-y02,x01-x02) # Reference flight direction for each line
            exp_num2=sorted_rds[i+1][57] #####changed
            expnum_diff=exp_num2-exp_num1 # Difference between two adjacent exposure no.
            x2=math.radians(sorted_rds[i+1][52]) #####changed
            y2=math.radians(sorted_rds[i+1][51]) #####changed
            theta=math.atan2(y1-y2,x1-x2)
            # threshold is photo width to decide if the consequent exposure points lying on the same flight
            dist_chk=calculateDistance(x1,y1,x2,y2)
            if ((expnum_diff <=1)and(dist_chk<rad_photo*2)):
                thetaFlt=theta
            else:
                # print (' Exposure number: %s' %exp_num2)
                thetaFlt=theta0
            #thetaFlt=theta
            #arcpy.AddMessage("Theta: %s"%thetaFlt)

        thetaFlt=theta # For the last point of each flight line
        row_old=[]
        lk=0
        # restored the existed fields before adding "8" created fileds
        for lk in range(0,(len_fields-8)):
            row_old.append(sorted_rds[i][lk])
            lk +=1
        # computed 4 corner points
        x11=math.degrees(x1+rad_photoS*math.cos(thetaFlt+math.pi/4.0))
        y11=math.degrees(y1+rad_photoS*math.sin(thetaFlt+math.pi/4.0))
        x22=math.degrees(x1+rad_photoS*math.cos(thetaFlt+math.pi/4.0+math.pi/2.0))
        y22=math.degrees(y1+rad_photoS*math.sin(thetaFlt+math.pi/4.0+math.pi/2.0))
        x33=math.degrees(x1+rad_photoS*math.cos(thetaFlt+math.pi/4.0+math.pi))
        y33=math.degrees(y1+rad_photoS*math.sin(thetaFlt+math.pi/4.0+math.pi))
        x44=math.degrees(x1+rad_photoS*math.cos(thetaFlt+math.pi/4.0+1.5*math.pi))
        y44=math.degrees(y1+rad_photoS*math.sin(thetaFlt+math.pi/4.0+1.5*math.pi))
        ang_qt=thetaFlt+math.pi/4.0
        # arrange the sequence of corner points following the order of
        # UR_X, UR_Y, UL_X, UL_Y, LL_X, LL_Y, LR_X, and LR_Y
        if (ang_qt>=0.0) & (ang_qt<(math.pi/2.0)):
            row_old=row_old+([x11,y11,x22,y22,x33,y33,x44,y44])
        elif ( (ang_qt>=(math.pi/2.0)) & (ang_qt<math.pi) ) | ( (ang_qt>=(-1.5*math.pi)) & (ang_qt<(-1.0*math.pi)) ):
            row_old=row_old+([x44,y44,x11,y11,x22,y22,x33,y33])
        elif ( (ang_qt>=(-1.0*math.pi)) & (ang_qt<(-1.0*(math.pi/2.0))) ) | ( (ang_qt>=math.pi) & (ang_qt<1.5*math.pi)):
            row_old=row_old+([x33,y33,x44,y44,x11,y11,x22,y22])
        else:
            row_old=row_old+([x22,y22,x33,y33,x44,y44,x11,y11])

        row_new.append(row_old)
        coord_pt.append([x11,y11])
        coord_pt.append([x22,y22])
        coord_pt.append([x33,y33])
        coord_pt.append([x44,y44])
        i +=1

    return [row_new, coord_pt]

def calculateDistance(x1,y1,x2,y2):
     dist = math.sqrt((x2 - x1)**2 + (y2 - y1)**2)
     return dist

## Function for building a polygon dataset from the photo corner coordinates. Written by ifer. Runs slowly!
def BuildPolys():

    #Build the four line files needed (each side of the polygon)
    try:
        # "","","","","","","","LR_LAT"
        arcpy.XYToLine_management(fc, "APSIselect_XYToLine_NEtNW", "UR_LON", "UR_LAT", "UL_LON", "UL_LAT", "GEODESIC", None, spatialRef)
        arcpy.XYToLine_management(fc, "APSIselect_XYToLine_NWtSW", "UL_LON", "UL_LAT", "LL_LON", "LL_LAT", "GEODESIC", None, spatialRef)
        arcpy.XYToLine_management(fc, "APSIselect_XYToLine_SWtSE", "LL_LON", "LL_LAT", "LR_LON", "LR_LAT", "GEODESIC", None, spatialRef)
        arcpy.XYToLine_management(fc, "APSIselect_XYToLine_SEtNE", "LR_LON", "LR_LAT", "UR_LON", "UR_LAT", "GEODESIC", None, spatialRef)
        #list needed later for iterating through to get single features
        fclist = ["APSIselect_XYToLine_NEtNW","APSIselect_XYToLine_NWtSW","APSIselect_XYToLine_SWtSE","APSIselect_XYToLine_SEtNE"]

    except Exception as e:
        print(e)
        print("!Cannot build line files from generated four corner coordinates. Consult ifer.")
        arcpy.AddWarning(" Cannot build line files from generated four corner coordinates. Consult ifer.")
        exit

    #Create a new, empty feature class for the final polgyons & track id field
    arcpy.CreateFeatureclass_management(fgdbTmp,footprntfn,"POLYGON","","DISABLED","DISABLED",spatialRef)
    arcpy.AddField_management(footprntfn,"ref_ID","LONG")

    #go through each input line file by OBJECTID, build a merged line dataset based on the same OID,
    #convert it to a polygon, append to the final polygon dataset, & pull in attributes from original point file
    try:
        Scursor = arcpy.da.SearchCursor(fc,"OBJECTID")
        for row in Scursor:
            featnum = row[0]
            n = 1
            for linefc in fclist:
                arcpy.MakeFeatureLayer_management(linefc,"line_"+str(n),"OID = "+str(featnum))
                n = n+1
            arcpy.Merge_management("line_1;line_2;line_3;line_4","Lines_Merged")
            arcpy.FeatureToPolygon_management("Lines_Merged","PolygonTemp")
            arcpy.AddField_management("PolygonTemp","ref_ID","LONG")
            arcpy.CalculateField_management("PolygonTemp","ref_ID",str(featnum),"PYTHON_9.3")
            arcpy.Append_management("PolygonTemp",footprntfn, "NO_TEST")


        #Transfer over attributes (if the software lets you).
        try:
            arcpy.JoinField_management(footprntfn,"ref_ID", fc,"OBJECTID",["PROJECT_CODE","VENDOR_ID","ROLL_NUMBER","FLIGHT_LINE","EXPOSURE_NUMBER","FILM_TYPE","PHOTO_SCALE","PROJECT_YEAR","PHOTO_DATE","STATE","LABELPC","LONGITUDE","LATITUDE","KEY_","EROS_Status","Scan_Status","NE_Long","NE_Lat","NW_Long","NW_Lat","SW_Long","SW_Lat","SE_Long","SE_Lat"])
            #arcpy.Delete_management(fc)
            arcpy.DeleteField_management(footprntfn,"ref_ID")
        except:
            try:
                arcpy.JoinField_management(footprntfn,"ref_ID", fc,"OBJECTID","PROJECT_CODE;VENDOR_ID;ROLL_NUMBER;FLIGHT_LINE;EXPOSURE_NUMBER;FILM_TYPE;PHOTO_SCALE;PROJECT_YEAR;PHOTO_DATE;STATE;LABELPC;LONGITUDE;LATITUDE;KEY_;EROS_Status;Scan_Status;NE_Long;NE_Lat;NW_Long;NW_Lat;SW_Long;SW_Lat;SE_Long;SE_Lat")
                #arcpy.Delete_management(fc)
                arcpy.DeleteField_management(footprntfn,"ref_ID")
            except:
                print("Joining the original attributes did not work. You will need to manually join attributes from APSISelect fc via the OBJECTID to the ref_ID.")
                arcpy.AddWarning("Joining the original attributes did not work. You will need to manually join need attributes from APSISelect fc via the OBJECTID to the ref_ID.")

        #Clean up if the polygon creation works well.
        arcpy.Delete_management("Lines_Merged")
        arcpy.Delete_management("PolygonTemp")
        arcpy.Delete_management("APSIselect_XYToLine_NEtNW")
        arcpy.Delete_management("APSIselect_XYToLine_NWtSW")
        arcpy.Delete_management("APSIselect_XYToLine_SWtSE")
        arcpy.Delete_management("APSIselect_XYToLine_SEtNE")
        arcpy.Delete_management(outfc)


        arcpy.AddMessage("Final Polygon dataset in designated fgdb.")
        print("Final Polygon dataset in designated fgdb.")

    except:
        print("!Cannot build polygons from the line features. Ask ifer. She wrote this part of the script.")
        arcpy.AddWarning("!Cannot build polygons from the line features. Ask ifer. She wrote this part of the script.")

def LoadLayer():
    try:
        #If user is in ArcGIS Pro
        aprx = arcpy.mp.ArcGISProject("CURRENT")
        # Look if there's an active map.  If there isn't, i.e. m == None, then just skip the symbology.
        m = aprx.activeMap
        ##arcpy.SaveToLayerFile(footprntfn, out_layer)
        m.addDataFromPath(os.path.join(fgdbTmp,footprntfn))
##            lyrnm = arcpy.mp.Layer(footprntfn)
##            m.addLayer(lyrnm, "TOP")
        ref_lyrx = r"T:\OC\GEOSpSection\NATL\Aerial_Imagery\_gis\APSI\AK\_Updating_API_Table\Air_Photo_Footprints.lyrx" 
        out_fc_lyr = m.listLayers()[0]
        arcpy.ApplySymbologyFromLayer_management(out_fc_lyr, ref_lyrx)
        arcpy.SetParameterAsText(4, out_fc_lyr)
    except Exception as e:
        arcpy.AddWarning(e)
        arcpy.AddWarning("!New Footprint file could not be added to your current map.")

# Run the script
if __name__ == '__main__':
    if int(arcpy.GetCount_management(fc).getOutput(0))>0:
        main ()  #Runs Ernie's functions to populate a fc with four corner lat/long coordinates.
        print(" Building Photo Corner Polygons. This may take a bit. Be patient.")
        if makePolys:
            arcpy.AddMessage(" Building Photo Corner Polygons. This may take a bit. Be patient.")
            BuildPolys()
        print("--Finished--")
        arcpy.AddMessage("--Finished--")
        arcpy.Delete_management(fc)
        if standalone != "Y":
            if makePolys:
                LoadLayer()
    else:
        arcpy.Delete_management(fc)
        print("SQL statement yeilded no selected features from the APSI source. Exiting")
        arcpy.AddError("SQL statement yeilded no selected features from the APSI source. Exiting")
