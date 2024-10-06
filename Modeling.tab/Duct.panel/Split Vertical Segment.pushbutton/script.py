
import clr 
import math
from pyrevit import revit,forms,script

clr.AddReference('RevitAPI')
import Autodesk
from Autodesk.Revit.DB import *

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
selection = uidoc.Selection
#-------------------------------------------------------------------------------
class SelectionFilter(ISelectionFilter):
    def __init__(self, categories):
        self.categories = categories

    def AllowElement(self, element):
        if element.Category.Name in self.categories:
            return True
        return False

    def AllowReference(self, reference, point):
        return False
        
def ToLst(ele):
    if isinstance(ele,list):
        return ele
    else:
        return [ele]

def Flatten_lv3 (lst):
    return [i for sub_lst in lst for i in sub_lst]

def AllElementsOfCategoryInView(categories):
	categories = ToLst(categories)
	allcates = doc.Settings.Categories
	valid_cate = []
	alleles = []
	for cate in allcates:
		for category in categories:
			if cate.Name == category:
				valid_cate.append(cate)

	for cate in valid_cate:
		alleles.append(FilteredElementCollector(doc,view.Id).OfCategoryId(cate.Id).WhereElementIsNotElementType().ToElements())

	return Flatten_lv3(alleles)

def IntersectionPlaneAndLine(plane,line):
    planePoint = plane.Origin
    planeNormal = plane.Normal
    lineStart = line.GetEndPoint(0)
    lineEnd = line.GetEndPoint(1)
    lineDirection = (lineEnd - lineStart).Normalize()

    # Check if the line is parallel to the plane
    # If yes, return None
    if planeNormal.DotProduct(lineDirection) == 0:
        return None
    
    lineParameter = (planeNormal.DotProduct(planePoint) - planeNormal.DotProduct(lineStart)) / planeNormal.DotProduct(lineDirection)

    return lineStart + lineParameter * lineDirection

def IsPointOnLine(point,line):
    # If a point C is on a line, it will be between start point(A) and end point(B) of a line
    # AB = AC + CB
    lineStart = line.GetEndPoint(0)
    lineEnd = line.GetEndPoint(1)
    lineLength = lineStart.DistanceTo(lineEnd)
    startToPoint = lineStart.DistanceTo(point)
    pointToEnd = point.DistanceTo(lineEnd)

    if lineLength == startToPoint + pointToEnd:
        return True
    else:
        return False

def GetZCoordinate(point):
    return point.Z

def SortPointByElevation(points):
    return sorted(points, key=GetZCoordinate)

def SortPointByLineDirection(line,lstPoint):
    direction = line.Direction
    vectorZ = direction.Z
    sortedPoints = SortPointByElevation(lstPoint)
    if vectorZ > 0:
        return sortedPoints
    else:
        return list(reversed(sortedPoints))

def SplitPipeByPoint(pipe,pts):
    ele = []
    with Transaction(doc,'Break Curve') as t:
        t.Start()
        result = []
        for pt in pts:
            try:
                ele.append(DB.Plumbing.PlumbingUtils.BreakCurve(doc,pipe.Id,pt))
            except Exception as er:
                result.append(er)
        ele.append(pipe.Id)
        result = [doc.GetElement(Id) for Id in ele]
        t.Commit()
    return result

def SplitDuctByPoint(duct,pts):
    ele = []
    result = []
    with Transaction(doc,'Break Curve') as t:
        t.Start()
        for pt in pts:
            try:
                ele.append(DB.Mechanical.MechanicalUtils.BreakCurve(doc,duct.Id,pt))
            except Exception as er:
                result.append(er)
        ele.append(duct.Id)
        result = [doc.GetElement(Id) for Id in ele]
        t.Commit()
    return result

def ClosestConnectors(ele1, ele2):
	conn1 = ele1.ConnectorManager.Connectors
	conn2 = ele2.ConnectorManager.Connectors
	
	dist = 100000000
	connset = None
	for c in conn1:
		for d in conn2:
			conndist = c.Origin.DistanceTo(d.Origin)
			if conndist < dist:
				dist = conndist
				connset = [c,d]
	return connset

def CreateUnionFitting(ele1,ele2):
    connectors = ClosestConnectors(ele1,ele2)
    result = []
    with Transaction(doc,'Create Union Fitting') as t:
        t.Start()
        try:
            result.append(doc.Create.NewUnionFitting(connectors[0],connectors[1]))
        except Exception as er:
            result.append(er)
        t.Commit()
    return result

#----------------------------Main Logic-----------------------------------------
# Select duct and pipe
filterEle = SelectionFilter(["Ducts","Pipes"])
refEle = selection.PickObjects(ObjectType.Element, filterEle, "Select Model Elements")
selectedEle = []
for sublst in refEle:
    selectedEle.append(doc.GetElement(sublst))


eleLine = []
for ele in selectedEle:
    line = ele.Location.Curve
    eleLine.append(line)

# Get all levels in view
allLevels = AllElementsOfCategoryInView("Levels")
levelElevations = [level.Elevation for level in allLevels]

# Create planes from levels
planeLst = []
z_axis = XYZ(0,0,1)
for elevation in levelElevations:
    plane = Plane.CreateByNormalAndOrigin(z_axis,XYZ(0,0,elevation))
    planeLst.append(plane)

# Get intersection points between line and plane
intersectionPoint = []
for line in eleLine:
    sublst = []
    for plane in planeLst:
        point = IntersectionPlaneAndLine(plane,line)
        if IsPointOnLine(point,line):
            sublst.append(point)
    intersectionPoint.append(SortPointByLineDirection(line,sublst))


#----------------------------------Split Vertical Segment-----------------------------------------------------------------
with TransactionGroup(doc,'Split Vertical Segment') as tg:
    tg.Start()

    newEles = []
    newEles2 = []
    for ele,sub_lst in zip(selectedEle,intersectionPoint):
        if isinstance(ele,Autodesk.Revit.DB.Plumbing.Pipe):
            newEles = SplitPipeByPoint(ele,sub_lst)
            newEles2 = newEles[1:]
        else:
            newEles = SplitDuctByPoint(ele,sub_lst)
            newEles2 = newEles[1:]

        for ele1,ele2 in zip(newEles,newEles2):
            CreateUnionFitting(ele1,ele2)

    print ('Done')
    tg.Assimilate()