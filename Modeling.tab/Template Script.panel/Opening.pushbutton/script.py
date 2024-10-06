from ast import Sub
import clr 
import math
import xlsxwriter
import os
import collections
from pyrevit import revit,forms,script
from pyrevit.forms import ProgressBar
from Autodesk.Revit.UI.Selection import ObjectType 
from System.Collections.Generic import *
from rpw.ui.forms import Alert

clr.AddReference('ProtoGeometry')
import Autodesk.DesignScript.Geometry as DSGeo
from Autodesk.DesignScript.Geometry import *

clr.AddReference('RevitAPI')
import Autodesk
from Autodesk.Revit.DB import *

clr.AddReference('RevitAPIUI')
from  Autodesk.Revit.UI import*
from  Autodesk.Revit.UI.Selection import*

clr.AddReference('RevitServices')
import RevitServices
from RevitServices.Persistence import DocumentManager
from RevitServices.Transactions import TransactionManager

import System.Drawing
import System.Windows.Forms
import collections

from System.Drawing import *
from System.Windows.Forms import *
from Opening.core import *

doc = __revit__.ActiveUIDocument.Document
view = doc.ActiveView
uidoc = __revit__.ActiveUIDocument
app = __revit__.Application
DB = Autodesk.Revit.DB
output = script.get_output()
unit = doc.GetUnits()
version = int(app.VersionNumber)
selection = uidoc.Selection

#-----------------------------------Get Neccessary Infomation-----------------------------------------------------------
# Intinitial input
offset = 50
openingName = ["Rectangular Opening"]

# Select Wall
filterWall = SelectionFilter(["Walls"])
refWall = selection.PickObject(ObjectType.Element, filterWall, "Select Wall")
selectedWall = doc.GetElement(refWall.ElementId)
wallGeometry = GetGeometryOfElement(selectedWall)
wallSolid = GetSolidfromGeo(wallGeometry)


# Select model element
filterEle = SelectionFilter(["Ducts","Pipes","Duct Accessories"])
refEle = selection.PickObjects(ObjectType.Element, filterEle, "Select Model Elements")
selectedEle = []
for sublst in refEle:
    selectedEle.append(doc.GetElement(sublst.ElementId))
eleGeometry = [GetGeometryOfElement(ele) for ele in selectedEle]
eleSolid = Flatten_lv3([GetSolidfromGeo(geo) for geo in eleGeometry])



# Intersect
# intersectSolids = []
# for solid in eleSolid:
#     intersectSolid = GeometryIntersect(wallSolid[0],solid)
#     intersectSolids.append(intersectSolid)
    # CreateBoundingBox(intersectSolid)

# print (intersectSolids)


# unionSolid = UnionSolids(intersectSolids)
unionSolid = UnionSolids(wallSolid[0],eleSolid)
unionBoundingbox = GetBoundingBoxGeometry(unionSolid)

'''Test'''
LENGTH_UNIT = doc.GetUnits().GetFormatOptions(SpecTypeId.Length).GetUnitTypeId()
scale = Transform.Identity.ScaleBasisAndOrigin(
    UnitUtils.ConvertFromInternalUnits(1, LENGTH_UNIT)
)
centroid = unionSolid.ComputeCentroid()
unit_centroid = scale.OfPoint(centroid)


print (unit_centroid)
# CreateSolid(unionSolid)
# Get place point
centerBoundingbox = GetCenterBoundingBox(unionBoundingbox)
# print (centerBoundingbox)

# Get face of wall to host
wallFaces = GetFacefromSolid(wallSolid)
maxFace = GetMaxAreaFace(wallFaces)[0]


# Rotate the union solid to get the correct bounding box aligned with wall
unionOrigin = GetCentroidSolid(unionSolid) # Get the origin to rate
zAxis = XYZ.BasisZ

wallDirection = GetElementDirection(selectedWall)
xAxis = XYZ.BasisX
angle = -(AngleAboutAxis(xAxis,wallDirection,zAxis)) # Get the angle to rotate


rotatedSolid = RotateGeometry(unionSolid,unionOrigin,zAxis,angle) # Rotate the union solid

rotatedBoundingbox = GetBoundingBoxGeometry(rotatedSolid[0])
minPointBoundingbox = GetMinPoint(rotatedBoundingbox)
maxPointBoundingbox = GetMaxPoint(rotatedBoundingbox)


# Calculate dimensions of opening
widthBoundingbox = maxPointBoundingbox.X - minPointBoundingbox.X
heightBoundingbox = maxPointBoundingbox.Z - minPointBoundingbox.Z
widthOpening = widthBoundingbox + convertToFeet(offset)*2
heightOpening = heightBoundingbox + convertToFeet(offset)*2

# widthOpening = widthBoundingbox
# heightOpening = heightBoundingbox

wallType = GetElementType(doc,selectedWall)
thicknessOpening = wallType.LookupParameter("Width").AsDouble()


# Get the opening family type
editableFamilies = GetEditableFamily(doc)
familyNames = [family.Name for family in editableFamilies]
familyDict = dict(zip(familyNames,editableFamilies))
for name in openingName:
    if name in familyNames:
        openingFamily = familyDict.get(name)
        openingFamilyType = GetFamilySymbolFromFamily(openingFamily)

#Dimension of opening
# print (convertToMilimeter(heightOpening))
# print (convertToMilimeter(widthOpening))

#Create bounding box of roated solid
# CreateBoundingBox(rotatedBoundingbox)

#Centroid of the solid after rotating
# print (convertToMilimeter(centerBoundingbox.X))
# print (convertToMilimeter(centerBoundingbox.Y))
# print (convertToMilimeter(centerBoundingbox.Z))
# print (convertToMilimeter(widthOpening))
# print (convertToMilimeter(heightOpening))

#---------------------------------Place Opening-------------------------------------------------------------------------
# with TransactionGroup(doc,"Place Wall Opening") as tg:
#     tg.Start()
#     opening = PlaceFamilyInstanceByFaceAndPoint(maxFace,openingFamilyType,centerBoundingbox)

#     # Set dimensions for opening
#     SetParameterByName(opening,"Width",widthOpening)
#     SetParameterByName(opening,"Height",heightOpening)
#     SetParameterByName(opening,"Depth",thicknessOpening)


#     tg.Assimilate()
