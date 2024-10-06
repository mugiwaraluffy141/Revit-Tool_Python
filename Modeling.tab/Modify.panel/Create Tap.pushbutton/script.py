import clr
import Autodesk.Revit.Exceptions
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
    
def ClosetConnectorsTap(pipe1, pipe2):
	conn1 = pipe1.ConnectorManager.Connectors
	line = pipe2.Location.Curve
	
	dist = 100000000
	conn = None
	for c in conn1:
		conndist = line.Project(c.Origin).Distance
		if conndist < dist:
			dist = conndist
			conn = c
	return conn

def CreateTap(branchEles,mainEle):
    result = []
    for pipe in branchEles:
        connectors = ClosetConnectorsTap(pipe,mainEle)
        with Transaction(doc,'Create Tap') as t:
            t.Start()
            try:
                result.append(doc.Create.NewTakeoffFitting(connectors,mainEle))
            except:
                pass
            t.Commit()
    return result

#---------------------------Main Logic------------------------------------------
with TransactionGroup(doc,"Create Tap") as tg:
    tg.Start()
    try:
        while True:
            # Main element
            filterMainEle = SelectionFilter(["Ducts","Pipes"])
            refMainEle = selection.PickObject(ObjectType.Element, filterMainEle, "Select Main Element")
            mainEle = doc.GetElement(refMainEle)
            mainCate = mainEle.Category.Name


            # Branch elements
            filterBranchEles = SelectionFilter([mainCate],mainEle.Id)
            refBranchEles = selection.PickObjects(ObjectType.Element, filterBranchEles, "Select Branch Elements")
            branchEles = []
            for sublst in refBranchEles:
                branchEles.append(doc.GetElement(sublst))

            #Create Tap
            CreateTap(branchEles,mainEle)

    except Autodesk.Revit.Exceptions.OperationCanceledException:
        pass
    tg.Assimilate()