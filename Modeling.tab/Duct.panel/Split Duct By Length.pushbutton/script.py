'''
Function: Split The Duct By Length
-----------------------------------------------------------------
User Manual: Enter the length of duct
-----------------------------------------------------------------
'''
import clr 
import math
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
#-------------------------------------------------------------------------------      
def tolst(ele):
    if isinstance(ele,list):
        return ele
    else:
        return [ele]

def flatten_lv3 (lst):
    return [i for sub_lst in lst for i in sub_lst]

def AllElementOfCategoryInView(categories):
	categories = tolst(categories)
	allcates = doc.Settings.Categories
	valid_cate = []
	alleles = []
	for cate in allcates:
		for category in categories:
			if cate.Name == category:
				valid_cate.append(cate)

	for cate in valid_cate:
		alleles.append(FilteredElementCollector(doc,view.Id).OfCategoryId(cate.Id).WhereElementIsNotElementType().ToElements())

	return flatten_lv3(alleles)

def CurveAtSegmentLength(eles,distance,unionThickness):
    result = []
    for ele,thickness in zip(eles,unionThickness):
        #Get direction of element
        direct = ele.Location.Curve.Direction
        point = ele.Location.Curve.GetEndPoint(0)

        #Divide length into pieces
        length = ele.LookupParameter('Length').AsDouble()*304.8
        section = int(length/distance)
        sub_lst = []
        scale = 0
        
        for i in range(0,section):
            if i == 0:
                scale += distance + thickness/2
            elif i > 0:
                scale += distance + thickness
            
            vectorDist = direct.Multiply(scale/304.8)
            newpoint = point.Add(vectorDist)
            sub_lst.append(newpoint)
        result.append(sub_lst)

    return result

def splitDuctByPoint(duct,pts):
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

def closestConnectors(ele1, ele2):
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

def createUnionFitting(ele1,ele2):
    connectors = closestConnectors(ele1,ele2)
    result = []
    with Transaction(doc,'Create Union Fitting') as t:
        t.Start()
        try:
            result.append(doc.Create.NewUnionFitting(connectors[0],connectors[1]))
        except Exception as er:
            result.append(er)
        t.Commit()
    return result

def GetDuctUnionFamily(duct):
    manager = duct.DuctType.RoutingPreferenceManager
    ruleUnion = manager.GetRule(RoutingPreferenceRuleGroupType.Unions , 0)
    unionType = doc.GetElement(ruleUnion.MEPPartId).Family
    return unionType

def GetConnectorsFromDocument(doc):
	connectors = FilteredElementCollector(doc).OfCategory(BuiltInCategory.OST_ConnectorElem).WhereElementIsNotElementType().ToElements()
	return connectors

def GetUnionThickness(unionFamily):
    familyDoc =  doc.EditFamily(unionFamily)
    familyConnector = GetConnectorsFromDocument(familyDoc)
    connectorPoint1 = familyConnector[0].Origin
    connectorPoint2 = familyConnector[1].Origin
    distanceConnector = round(connectorPoint1.DistanceTo(connectorPoint2)*304.8)
    return distanceConnector

#----------------------------Main Logic-----------------------------------------
#Enter duct length
distance = forms.ask_for_string(
    default='1',
    prompt='Enter Duct Length (mm)',
    title='Duct Length'
)
distance = int(distance)

#Filter valid duct
ductInView = AllElementOfCategoryInView('Ducts')
ductLength = [duct.LookupParameter('Length').AsDouble()*304.8 for duct in ductInView]
ductUnion = [GetDuctUnionFamily(duct) for duct in ductInView]
unionThickness = [GetUnionThickness(union) for union in ductUnion]

validDuct = []
for duct,length in zip(ductInView,ductLength):
    family = duct.LookupParameter('Family').AsValueString()
    if length > (distance + 1) and family == 'Rectangular Duct':
        validDuct.append(duct)

ductLine = [duct.Location.Curve for duct in validDuct]
startpoints = [line.GetEndPoint(0) for line in ductLine]

#Create a list of distances
pts = CurveAtSegmentLength(validDuct,distance,unionThickness)

#----------------------------------Split Duct by Length-----------------------------------------------------------------
with TransactionGroup(doc,'Split Duct by Length') as tg:
    tg.Start()

    newEles = []
    newEles2 = []
    for duct,sub_lst in zip(validDuct,pts):
        newEles = splitDuctByPoint(duct,sub_lst)
        newEles2 = newEles[1:]

        for ele1,ele2 in zip(newEles,newEles2):
            createUnionFitting(ele1,ele2)

    print ('Done')
    tg.Assimilate()