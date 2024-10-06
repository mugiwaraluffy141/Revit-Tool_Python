
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

def all_ele_of_cate_in_view(categories):
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

def curveAtSegmentLength(eles,distance):
    result = []
    for ele in eles:
        #Get direction of element
        direct = ele.Location.Curve.Direction
        point = ele.Location.Curve.GetEndPoint(0)

        #Divide length into pieces
        length = ele.LookupParameter('Length').AsDouble()*304.8
        section = int(length/distance)
        sub_lst = []
        flag = 0
        
        for i in range(0,section):
            if i == 0:
                flag += distance + unionThickness/2
            elif i > 0:
                flag += distance + unionThickness
            
            vectorDist = direct.Multiply(flag/304.8)
            newpoint = point.Add(vectorDist)
            sub_lst.append(newpoint)
        result.append(sub_lst)

    return result

def splitPipeByPoint(pipe,pts):
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


#----------------------------Main Logic-----------------------------------------
#Enter pipe length
distance = forms.ask_for_string(
    default='1',
    prompt='Enter Pipe Length',
    title='Pipe Length'
)
distance = int(distance)
unionThickness = 77.8

#Filter valid pipe
pipeInView = all_ele_of_cate_in_view('Pipes')
# print (pipeInView)
pipeLength = [pipe.LookupParameter('Length').AsDouble()*304.8 for pipe in pipeInView]
# print (pipeLength)

validPipe = []
for pipe,length in zip(pipeInView,pipeLength):
	if length > (distance + 1):
		validPipe.append(pipe)
# print (validPipe)

pipeLine = [pipe.Location.Curve for pipe in validPipe]
startpoints = [line.GetEndPoint(0) for line in pipeLine]

#Create a list of distances
pts = curveAtSegmentLength(validPipe,distance)
# print (pts)


#----------------------------------Split Pipe by Length-----------------------------------------------------------------

with TransactionGroup(doc,'Split Pipe by Length') as tg:
    tg.Start()

    newEles = []
    newEles2 = []
    for pipe,sub_lst in zip(validPipe,pts):
        newEles = splitPipeByPoint(pipe,sub_lst)
        newEles2 = newEles[1:]

        for ele1,ele2 in zip(newEles,newEles2):
            createUnionFitting(ele1,ele2)

    print ('Done')
    tg.Assimilate()