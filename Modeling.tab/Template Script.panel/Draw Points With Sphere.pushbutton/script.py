#!/usr/bin/env python
# -*- coding: utf-8 -*-
'''
Function: A Code Snippet To Draw Points With Sphere
Note: Alt + Left Click to get the family Sphere
-----------------------------------------------------------------
User Manual: Click To Run
-----------------------------------------------------------------
'''
from Autodesk.Revit.DB.Structure import StructuralType
import clr 
from pyrevit import revit,forms,script


clr.AddReference('RevitAPI')
import Autodesk
from Autodesk.Revit.DB import *

doc = __revit__.ActiveUIDocument.Document
view = doc.ActiveView
uidoc = __revit__.ActiveUIDocument
app = __revit__.Application
DB = Autodesk.Revit.DB
output = script.get_output()
unit = doc.GetUnits()
version = int(app.VersionNumber)
selection = uidoc.Selection
#-----------------------------Function------------------------------------------
def ToLst(ele):
	if isinstance(ele,list):
		return ele
	else:
		return [ele]

def Flattenlv3(ele):
	return [j for i in ele for j in i]
	
def AllElementsOfCategoryInView(categoryNames,view):
	categoryNames = ToLst(categoryNames)
	allcates = doc.Settings.Categories
	valid_cate = []
	alleles = []
	for cate in allcates:
		for category in categoryNames:
			if cate.Name == category:
				valid_cate.append(cate)

	for cate in valid_cate:
		alleles.append(FilteredElementCollector(doc,view.Id).OfCategoryId(cate.Id).WhereElementIsNotElementType().ToElements())

	return Flattenlv3(alleles)

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
        
def PlaceFamilyInstance(point,familySymbol):
    structuralType = StructuralType.NonStructural
    with Transaction(doc,"Place Family Instance") as t:
        t.Start()
        newInstance = doc.Create.NewFamilyInstance(point,familySymbol,structuralType)
        t.Commit()
    return newInstance

#-----------------------------Main Logic----------------------------------------
# Get points
elements = AllElementsOfCategoryInView("Air Terminals",view)
points = [ele.Location.Point for ele in elements]

# Get Sphere family
sphereFamily = GetFamilyByName("Sphere")
sphereType = GetFamilySymbolByName(sphereFamily,"Sphere")

#-----------------------------Execute-------------------------------------------
with TransactionGroup(doc,"Draw Points With Sphere") as tg:
    tg.Start()
    for point in points:
        PlaceFamilyInstance(point,sphereType)
    
    tg.Assimilate()
      
