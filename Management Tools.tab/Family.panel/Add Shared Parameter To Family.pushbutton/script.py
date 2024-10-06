#!/usr/bin/env python
# -*- coding: utf-8 -*-
'''
Function: Add Shared Parameter In A CSV File To Multiple Families In A Folder.
-----------------------------------------------------------------
Note: 
_ Alt + Left Click to see the Sample file
_ You must add the shared parameter file to your model before running the tool
-----------------------------------------------------------------
User Manual:
_ Step 1: Select a csv file
_ Step 2: Select a folder containing families
-----------------------------------------------------------------
'''
import clr 
from pyrevit import revit,forms,script
from rpw.ui.forms import Alert
import csv
import codecs

import System
clr.AddReference("System.Numerics")
from System.Collections.Generic import *
from System.Runtime.InteropServices import Marshal
from System.IO import Directory, SearchOption

clr.AddReference('RevitAPI')
import Autodesk
from Autodesk.Revit.DB import *

doc = __revit__.ActiveUIDocument.Document
view = doc.ActiveView
uidoc = __revit__.ActiveUIDocument
app = __revit__.Application
DB = Autodesk.Revit.DB
output = script.get_output()
version = app.VersionNumber

#----------------------------------------Method-------------------------------------------------------------------------
def Flatten_lv3 (lst):
    return [instance for sub_lst in lst for instance in sub_lst]

def ReadCSVFile(path):
    if not path:
        Alert('No CSV File Selected. Please Select Again.', exit=True)

    elif path:
        try:
            with codecs.open(path, 'r', encoding='utf-8-sig') as csvfile:
                fileContent = []
                f = csv.reader(csvfile)
                
                #Skip the header row
                next(f)
                
                for row in f:
                    fileContent.append(row)
        except:
            pass
    
    return fileContent

def DirectoryContent(directoryPath,searchString,deepSearch):
    result = []
    if Directory.Exists(directoryPath):
        if deepSearch:
            directoryFiles = Directory.GetFiles(directoryPath, ".", SearchOption.AllDirectories)
        else:
            directoryFiles = Directory.GetFiles(directoryPath, ".", SearchOption.TopDirectoryOnly)
        for file in directoryFiles:
            if searchString not in file:
                continue
            else:
                result.append(file)
        return result
    else:
        return [] 

def OpenDocumentFromPath(filePath):
    documents = []

    try:
        doc = app.OpenDocumentFile(filePath)
        documents.append(doc)
    except:
        documents.append(None)

    return documents

def CloseDocument(doc,saveOption):
    result = []
    try:
        doc.Close(saveOption)
        result.append(True)
    except:
        result.append(False)
    return result

def GetSharedParamInRevitDoc():
    paramDefinition = []
    paramName = []
    groupDefinition = []
    groupName = []

    file = app.OpenSharedParameterFile()
    groups = file.Groups

    for group in groups:
        for definition in group.Definitions:
            paramDefinition.append(definition)
            paramName.append(definition.Name)
            groupDefinition.append(group)
            groupName.append(group.Name)

    return paramDefinition,paramName,groupDefinition,groupName

def GetBuiltInParamGroupByName(name):
    builtinGroups = [a for a in System.Enum.GetValues(BuiltInParameterGroup)]
    builtinNames = [a.ToString() for a in System.Enum.GetValues(BuiltInParameterGroup)]

    result = []
    try:
        ind = builtinNames.index(name)
        result.append(builtinGroups[ind])
    except:
        result.append(None)
    
    return result


#------------------------------------Main logic-------------------------------------------------------------------------
#Import shared parameter excel
csvFilePath = forms.pick_file(file_ext='csv',title = "Select Shared Parameter Sheet")
csvData = ReadCSVFile(csvFilePath)
sharedParamName = [sublst[0] for sublst in csvData]
builtinParamGroupName = [sublst[2] for sublst in csvData]
builtinParamGroup = Flatten_lv3([GetBuiltInParamGroupByName(name) for name in builtinParamGroupName])
isInstanceParam = [True if sublst[3] == "Yes" else False for sublst in csvData]

#Get shared parameter in Application
sharedParamDefInApp = GetSharedParamInRevitDoc()[0]
sharedParamNameInApp = GetSharedParamInRevitDoc()[1]
sharedParamDict = dict(zip(sharedParamNameInApp,sharedParamDefInApp))
externalDefinitionParam = [sharedParamDict.get(name) for name in sharedParamName]

#Search families in folder
folderPath = forms.pick_folder(title = "Select Folder Containing Family",owner = False)
searchString = ".rfa"
deepSearch = True
familyPath = DirectoryContent(folderPath,searchString,deepSearch)
familyDocument = Flatten_lv3([OpenDocumentFromPath(path) for path in familyPath])


#----------------------------------------------Add shared parameter to family-------------------------------------------
result = []
saveOption = True
for doc in familyDocument:
    with Transaction(doc, 'Add Shared Parameter') as t:
        t.Start()
        for externalDef, builtinGroup, instance in zip(externalDefinitionParam, builtinParamGroup, isInstanceParam):
            try:
                new = doc.FamilyManager.AddParameter(externalDef, builtinGroup, instance)
            except:
                result.append(externalDef.Name)
        t.Commit()
    CloseDocument(doc,saveOption)

outcome = list(set(result))
if len(outcome) > 0 :
    for param in outcome:
        print ("Can not add this parameter: " + param)
else:
    print ("Done")