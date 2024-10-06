#!/usr/bin/env python
# -*- coding: utf-8 -*-
'''
Function: Place Family From CAD
Note: Alt + Left Click to see the Sample file
-----------------------------------------------------------------
User Manual:
_ Step 1: Select the CSV file
_ Step 2: Select CAD Link
-----------------------------------------------------------------
'''

import clr
import csv
import codecs
from pyrevit import revit,forms,script
from rpw.ui.forms import Alert

clr.AddReference('RevitAPI')
import Autodesk
from Autodesk.Revit.DB import *
from Autodesk.Revit.DB.Structure import *

clr.AddReference('RevitAPIUI')
from  Autodesk.Revit.UI import*
from  Autodesk.Revit.UI.Selection import*

doc = __revit__.ActiveUIDocument.Document
view = doc.ActiveView
uidoc = __revit__.ActiveUIDocument
app = __revit__.Application
DB = Autodesk.Revit.DB
output = script.get_output()
unit = doc.GetUnits()
version = int(app.VersionNumber)

#----------------------------------------------Function-----------------------------------------------------------------------
class CADFilter(ISelectionFilter):
    def AllowElement(self, element):
        if isinstance(element, ImportInstance):
            return True
        return False

    def AllowReference(self, reference, point):
        return False
    
def Flatten_lv3 (lst):
    return [i for sub_lst in lst for i in sub_lst] 

def GetCADLayerNames(cadFile):
    subCateLst = cadFile.Category.SubCategories
    result = [subCate.Name for subCate in subCateLst]
    return result

def GetGeometryFromLayerCAD(layerName,cadLinkType):
    result = []
    geoObject = cadLinkType.get_Geometry(Options())
    for geoOb in geoObject:
        try:
            graphicStyleId = geoOb.GraphicsStyleId
            eleGraphicStyle = doc.GetElement(graphicStyleId)
            eleGraphicStyleName = eleGraphicStyle.GraphicsStyleCategory.Name
            if layerName == eleGraphicStyleName:
                result.append(geoOb)
        except:
            pass
    return result

def GetCADName(cadLinkType):
    return cadLinkType.Category.Name

def GetBlockCADByName(blockName,cadLinkType):
    result = []
    cadName = GetCADName(cadLinkType)
    geometryElement = cadLinkType.get_Geometry(Options())

    for geometryOb in geometryElement:
        if geometryOb != None and isinstance(geometryOb, GeometryInstance):
            symbolName = geometryOb.Symbol.LookupParameter("Type Name").AsString()
            symbolName = symbolName.Replace(cadName + ".","")

            if blockName == symbolName:
                result.append(geometryOb)

    return result

def GetBlockPoint(lstBlockCad,cadTransform):
    result = []
    for block in lstBlockCad:
        origin = cadTransform.OfPoint(block.Transform.Origin)
        result.append(origin)
    
    return result

def GetLevelByName(levelName):
    allLevels = FilteredElementCollector(doc).OfClass(Level).WhereElementIsNotElementType().ToElements()
    for level in allLevels:
        name = level.Name
        if name == levelName:
            return level

def GetFamilyByName(familyName):
    allFamilies = FilteredElementCollector(doc).OfClass(Family).ToElements()
    for family in allFamilies:
        try:
            name = family.Name
            if familyName == name:
                return family
        except:
            return None
    
def GetFamilySymbolByName(family,typeName):
    typeIds = family.GetFamilySymbolIds()
    for Id in typeIds:
        familySymbol = doc.GetElement(Id)
        name = familySymbol.LookupParameter("Type Name").AsString()
        if typeName == name:
            return familySymbol
        
def PlaceFamilyInstance(point,familySymbol,level):
    structuralType = StructuralType.NonStructural
    with Transaction(doc,"Place Family Instance") as t:
        t.Start()
        newInstance = doc.Create.NewFamilyInstance(point,familySymbol,level,structuralType)
        t.Commit()
    return newInstance

#----------------------------------------------Main Logic-----------------------------------------------------------------------
#Select CSV
source_file = forms.pick_file(file_ext='csv')
if not source_file:
    Alert('No CSV File Selected. Please Select Again.', exit=True)

if source_file:
    try:
        with codecs.open(source_file, 'r', encoding='utf-8-sig') as csvfile:
            blockNames, familyNames, typeNames, levelNames, elevations   = [], [], [], [], []
            f = csv.reader(csvfile)
            
            # Skip the header row
            next(f)
            
            for row in f:
                blockNames.append(row[0])
                familyNames.append(row[1])
                typeNames.append(row[2])
                levelNames.append(row[3])
                elevations.append(row[4])
    except:
        pass

ref = uidoc.Selection.PickObject(ObjectType.Element,CADFilter(),"Select CAD Link")
cadFile = doc.GetElement(ref)
cadTransform = cadFile.GetTransform()
cadLinkType = doc.GetElement(cadFile.GetTypeId())
cadName = GetCADName(cadLinkType)

#----------------------------------------------Place Family-----------------------------------------------------------------------
with TransactionGroup(doc,"Place Family From CAD") as tg:
    tg.Start()
    for blockName, familyName, typeName, levelName, elevation in zip(blockNames, familyNames, typeNames, levelNames, elevations):
        cadBlock = GetBlockCADByName(blockName,cadLinkType)
        lstPoints = GetBlockPoint(cadBlock,cadTransform)
        family = GetFamilyByName(familyName)
        symbol = GetFamilySymbolByName(family,typeName)
        level = GetLevelByName(levelName)

        for point in lstPoints:
            newInstance = PlaceFamilyInstance(point,symbol,level)

            with Transaction(doc,'Set Param') as t:
                t.Start()
                newInstance.LookupParameter("Elevation from Level").Set(float(elevation)/304.8)
                t.Commit()
    
        notification = typeName + ": " + str(len(cadBlock)) + " elements"
        print (notification)
    
    print("----------------------------------------------")
    print ("Done")
    tg.Assimilate()