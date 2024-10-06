import Autodesk.Revit
import Autodesk.Revit.Exceptions
import clr 
from pyrevit import revit,forms,script
from pyrevit.forms import ProgressBar
from rpw.ui.forms import Alert

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
version = int(app.VersionNumber)
selection = uidoc.Selection
#-----------------------------Function------------------------------------------
class SelectionFilter(ISelectionFilter):
    def __init__(self, categories, mainEleId=None):
        self.categories = categories
        self.mainEleId = mainEleId

    def AllowElement(self, element):
        if element.Category.Name in self.categories and element.Id != self.mainEleId:
            return True
        return False

    def AllowReference(self, reference, point):
        return False
    
def GetElementLine(ele):
    return ele.Location.Curve

def IntersectionLineAndLine(mainLine,branchLine):
    mainOrigin = mainLine.Origin

    branchOrigin = branchLine.Origin
    branchLineDirection = branchLine.Direction

    # Calculate the projected points using list comprehension
    pullPoint = branchOrigin.Add(branchLineDirection.Multiply(branchLineDirection.DotProduct(mainOrigin) - branchLineDirection.DotProduct(branchOrigin)))

    return pullPoint

def IsPointOnLine(point, line):
    
    lineStart = line.GetEndPoint(0)
    lineEnd = line.GetEndPoint(1)

    vectorToPoint = point - lineStart

    lineVector = lineEnd - lineStart

    crossProduct = vectorToPoint.CrossProduct(lineVector)
    distance = crossProduct.GetLength() / lineVector.GetLength()

    tolerance = 0.1
    if distance < tolerance:
        return True
    else:
        return False

def GetIndexByLineDirection(line, points):
    # Get the start point of the line
    startPoint = line.GetEndPoint(0)
    
    # Create a list of tuples containing each point and its index
    pointsWithIndices = list(enumerate(points))
    
    # Sort the list of tuples based on the distance from the start point
    sortedIndices = sorted(pointsWithIndices, key=lambda x: startPoint.DistanceTo(x[1]))
    
    # Extract and return the sorted indices
    return [x[0] for x in sortedIndices]

def SortPointsByLineDirection(line, points):
    # Get the start point of the line
    startPoint = line.GetEndPoint(0)
    
    # Sort points based on their distance from the start point of the line
    sortedPoints = sorted(points, key=lambda pt: startPoint.DistanceTo(pt))
    
    return sortedPoints

def GetItemByIndex(indices,items):
    return [items[ind] for ind in indices]

def SplitMEPElement(doc, originEle, breakPoints):
    elements = []
    # Copy mepCurveToOptimize as newPipe and move to breakPoint
    with TransactionGroup(doc,"Split MEP Element") as tg:
        sublst = []
        tg.Start()
        for breakPoint in breakPoints:
            location = originEle.Location

            start = location.Curve.GetEndPoint(0)
            end = location.Curve.GetEndPoint(1)
            with Transaction(doc,"Copy Element") as t:
                t.Start()
                copiedEle = ElementTransformUtils.CopyElement(doc, originEle.Id, breakPoint - start)
                newId = copiedEle[0]
                t.Commit()

            # Shorten mepCurveToOptimize and newPipe (adjust endpoints)
            AdjustMEPLength(originEle, start, breakPoint)
            AdjustMEPLength(doc.GetElement(newId), breakPoint, end)

            # Get pair of elements for the creating Tee step
            # sublst = [originEle.Id.IntegerValue,doc.GetElement(newId).Id.IntegerValue]
            sublst = [originEle,doc.GetElement(newId)]

            # Assign new element to origin element for next run
            originEle = doc.GetElement(newId)

            elements.append(sublst)
        tg.Assimilate()

    return elements

def AdjustMEPLength(mep_curve, p1, p2):
    location = mep_curve.Location
    with Transaction(doc,"Adjust Length") as t:
        t.Start()
        location.Curve = Line.CreateBound(p1, p2)
        t.Commit()

def ClosestConectorsTee(ele1, ele2,ele3):
	conn1 = ele1.ConnectorManager.Connectors
	conn2 = ele2.ConnectorManager.Connectors
	conn3 = ele3.ConnectorManager.Connectors
	
	dist1 = 100000000
	dist2 = 100000000
	connset = []
	for c in conn1:
		for d in conn2:
			conndist = c.Origin.DistanceTo(d.Origin)
			if conndist < dist1:
				dist1 = conndist
				c1 = c
				d1 = d
		for e in conn3:
			conndist = c.Origin.DistanceTo(e.Origin)
			if conndist < dist2:
				dist2 = conndist
				e1 = e
		connset = [c1,d1,e1]
	return connset

def CreateTee(ele1,ele2,ele3):
    connectors = ClosestConectorsTee(ele1,ele2,ele3)
    result = []
    with Transaction(doc,'Create Tee') as t:
        t.Start()
        try:
            result.append(doc.Create.NewTeeFitting(connectors[0],connectors[1],connectors[2]))
        except Exception as er:
            print (er)
        t.Commit()
    return result

#---------------------------Main Logic------------------------------------------
with TransactionGroup(doc,"Create Tee") as tg:
    tg.Start()
    try:
        while True:
            # Main element
            filterMainEle = SelectionFilter(["Ducts","Pipes","Cable Trays"])
            refMainEle = selection.PickObject(ObjectType.Element, filterMainEle, "Select Main Element")
            mainEle = doc.GetElement(refMainEle)
            mainCate = mainEle.Category.Name
            mainLine = GetElementLine(mainEle)

            # Branch elements
            filterBranchEles = SelectionFilter([mainCate],mainEle.Id)
            refBranchEles = selection.PickObjects(ObjectType.Element, filterBranchEles, "Select Branch Elements")
            branchEles = []
            for sublst in refBranchEles:
                branchEles.append(doc.GetElement(sublst))

            # Get intersection points
            branchLines = [GetElementLine(ele) for ele in branchEles]
            intersectPoints = []
            for branchLine in branchLines:
                intersectPoint = IntersectionLineAndLine(mainLine,branchLine)
                if IsPointOnLine(intersectPoint,mainLine):
                    intersectPoints.append(intersectPoint)
            breakPoints = SortPointsByLineDirection(mainLine,intersectPoints)

            # Sort branch elements by main element direction
            indices = GetIndexByLineDirection(mainLine,intersectPoints)
            branchEles = GetItemByIndex(indices,branchEles) 

            #Create Tee
            newEles = SplitMEPElement(doc,mainEle,breakPoints)
            for sublst,branch in zip(newEles,branchEles):
                CreateTee(sublst[0],sublst[1],branch)

    except Autodesk.Revit.Exceptions.OperationCanceledException:
        pass
    tg.Assimilate()