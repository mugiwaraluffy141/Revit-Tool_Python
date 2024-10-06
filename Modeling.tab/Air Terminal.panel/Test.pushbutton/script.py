# -*- coding: utf-8 -*-
'''
Only work in 3D view
'''
import clr 
from pyrevit import revit,forms,script
from Autodesk.Revit.UI.Selection import ObjectType 
from System.Collections.Generic import *


clr.AddReference('RevitAPI')
import Autodesk
from Autodesk.Revit.DB import *
from  Autodesk.Revit.UI.Selection import*

doc = __revit__.ActiveUIDocument.Document
view = doc.ActiveView
uidoc = __revit__.ActiveUIDocument
app = __revit__.Application
DB = Autodesk.Revit.DB

#Class and Function
class SelectionFilter(ISelectionFilter):
    def __init__(self, category):
        self.category = category

    def AllowElement(self, element):
        return element.Category.Name == self.category

def get_elements_connector(elements):
    return [[i for i in element.MEPModel.ConnectorManager.Connectors] if hasattr(element, 'MEPModel') else [i for i in element.ConnectorManager.Connectors] if hasattr(element, 'ConnectorManager') else [] for element in elements]

def get_disconnected_elements(elements, connectors):
    return [element for element, sub_lst in zip(elements, connectors) for connector in sub_lst if not connector.IsConnected]

def get_connector_direction(elements):
    return [connector.CoordinateSystem.BasisZ for sub_lst in get_elements_connector(elements) for connector in sub_lst]

def get_element_location(elements):
    return [element.Location.Point for element in elements]

def ray_bounce_on_current_category(points, directions, view, category):
    valid_cate = next((cate for cate in doc.Settings.Categories if cate.Name == category), None)
    if valid_cate:
        all_ducts = FilteredElementCollector(doc, view.Id).OfCategoryId(valid_cate.Id).WhereElementIsNotElementType().ToElements()
        ducts_id = List[ElementId]([duct.Id for duct in all_ducts])
        ri = ReferenceIntersector(ducts_id, FindReferenceTarget.All, view)

        pts = []
        elems = []
        for point, direction in zip(points, directions):
            ref = ri.FindNearest(point, direction)
            if ref is None:
                pts.append(None)
                elems.append(None)
            else:
                refel = ref.GetReference()
                elems.append(doc.GetElement(refel.ElementId))
                pts.append(refel.GlobalPoint)

        return pts, elems

def connect_air_terminals_on_duct(airterminals, ducts):
    with TransactionGroup(doc, 'Re-connect RO') as tg:
        tg.Start()
        result = False
        for airterminal, duct in zip(airterminals, ducts):
            with Transaction(doc, 'Re-connect RO') as t:
                t.Start()
                result = Autodesk.Revit.DB.Mechanical.MechanicalUtils.ConnectAirTerminalOnDuct(doc, airterminal.Id, duct.Id)
                t.Commit()
        tg.Assimilate()
    return result

# Main logic
ele_filter = SelectionFilter('Air Terminals')
all_airterminals = uidoc.Selection.PickElementsByRectangle(ele_filter, 'Select')
get_RO = [i for i in all_airterminals if '430_Inspektionsöffnung' in i.LookupParameter('Family').AsValueString()]

connectors_RO = get_elements_connector(get_RO)
disconnect_RO = get_disconnected_elements(get_RO, connectors_RO)
direction_RO = get_connector_direction(disconnect_RO)
location_RO = get_element_location(disconnect_RO)
valid_duct = ray_bounce_on_current_category(location_RO, direction_RO, view, 'Ducts')[1]
connect_RO_on_Duct = connect_air_terminals_on_duct(disconnect_RO, valid_duct)

if connect_RO_on_Duct:
    print('Finish.')
