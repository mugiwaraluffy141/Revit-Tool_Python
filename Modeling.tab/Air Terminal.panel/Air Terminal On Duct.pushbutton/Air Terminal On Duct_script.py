'''
Function: Connect Air Terminal On Duct.
-----------------------------------------------------------------
User Manual:
_ Step 1: Select Air Terminals
-----------------------------------------------------------------
'''
import clr 
from pyrevit import revit,forms,script
from Autodesk.Revit.UI.Selection import ObjectType 
from System.Collections.Generic import *


clr.AddReference('RevitAPI')
import Autodesk
from Autodesk.Revit.DB import *
from  Autodesk.Revit.UI.Selection import*


clr.AddReference('RevitAPIUI')
from  Autodesk.Revit.UI import*

doc = __revit__.ActiveUIDocument.Document
view = doc.ActiveView
uidoc = __revit__.ActiveUIDocument
app = __revit__.Application
DB = Autodesk.Revit.DB
#---------------------------------------------------------------------------
#Select elements by Category
class selectionfilter(ISelectionFilter):
    def __init__(self,category):
        self.category = category

    def AllowElement(self, element):
        if element.Category.Name == self.category:
            return True
        else:
            return False
   
ele = selectionfilter('Air Terminals')
all_airterminals = uidoc.Selection.PickElementsByRectangle(ele,'Select')

#--------------------------------------------------------------------------
def tolist(input):
	if isinstance(input,list):
		return input
	else:
		return [input]

def GetElementConector(elements):
    result = []
    for element in elements:
        try:
            connectors = element.MEPModel.ConnectorManager.Connectors
        except:
            try:
                connectors = element.ConnectorManager.Connectors
            except:
                connectors = []
        result.append([i for i in connectors])
    return result

def GetDisconnectedElement(elements,connectors):
    result = []
    for element,sub_lst in zip(elements,connectors):
        for connector in sub_lst:
            if connector.IsConnected == False:
                result.append(element)
    return result

def GetConnectorDirection(elements):
    connectors = GetElementConector(elements)
    result = []
    for sub_lst in connectors:
        for connector in sub_lst:
            result.append(connector.CoordinateSystem.BasisZ)
    return result

def ElementLocation(elements):
    result = []
    for element in elements:
        result.append(element.Location.Point)
    return result

def RaybounceOnCurrentCategory(points,directions,view,category):
    allcate = doc.Settings.Categories
    for cate in allcate:
        if cate.Name == category:
            valid_cate = cate
    all_ducts = FilteredElementCollector(doc,view.Id).OfCategoryId(valid_cate.Id).WhereElementIsNotElementType().ToElements()
    ducts_Id = List[ElementId]([duct.Id for duct in all_ducts])
    ri = ReferenceIntersector(ducts_Id,FindReferenceTarget.All,view)

    pts = []
    elems = []
    for point,direction in zip(points,directions):
        ref = ri.FindNearest(point,direction)
        if ref == None:
            pts.append(None)
            elems.append(None)
        else:
            refel = ref.GetReference()
            elems.append(doc.GetElement(refel.ElementId))

            refp = refel.GlobalPoint
            pts.append(refp)
           
    return pts,elems

def ConnectAirTerminalOnDuct(airterminals,ducts):
    with TransactionGroup(doc,'Connect Air Terminals On Ducts') as tg:
        tg.Start()
        result = False
        for airterminal,duct in zip(airterminals,ducts):

            with Transaction(doc,'Connect Air Terminals On Ducts') as t:
                t.Start()
                
                result = Autodesk.Revit.DB.Mechanical.MechanicalUtils.ConnectAirTerminalOnDuct(doc,airterminal.Id,duct.Id)

                t.Commit()
        tg.Assimilate()
    return result

#----------------------------------------------------------------------------
airter_connectors = GetElementConector(all_airterminals)
disconnect_airter = GetDisconnectedElement(all_airterminals,airter_connectors)
connector_direction_airter = GetConnectorDirection(disconnect_airter)
airter_location = ElementLocation(disconnect_airter)
valid_duct = RaybounceOnCurrentCategory(airter_location,connector_direction_airter,view,'Ducts')[1]
connect_AirTer_on_Duct = ConnectAirTerminalOnDuct(disconnect_airter,valid_duct)

if connect_AirTer_on_Duct:
    print ('Connect Air Terminals On Ducts Successfully.')
