import clr 
from pyrevit import revit, forms


clr.AddReference('RevitAPI')
import Autodesk
from Autodesk.Revit.DB import *

clr.AddReference('RevitAPIUI')
from Autodesk.Revit.UI import*

doc = __revit__.ActiveUIDocument.Document
view = doc.ActiveView
uidoc = __revit__.ActiveUIDocument
app = __revit__.Application
#------------------------------------------------------

def SelectElemnt():
    Ob_type = Selection.ObjectType.Element
    ref = uidoc.Selection.PickObject(Ob_type,'Select model element')
    return doc.GetElement(ref.ElementId)


def getInstanceGeometry(dwg):
    GeoIns = []
    for i in dwg.Geometry[Options()]:
        for j in i.GetInstanceGeometry():
            GeoIns.append(j)
        return GeoIns

def getLineFromGeoIns(lstGeoIns):
    lines = []
    for i in lstGeoIns:
        if i.GetType() == Autodesk.Revit.DB.Line:
            lines.append(i)
    return lines

def getGraphicsStyleId(lstPlannar):
    re = []
    for i in lstPlannar:
        re.append(i.GraphicsStyleId)
    return re

def getGraphicStyleCategory(lstId):
    grapStyCate = []
    grapSty = []
    for i in lstId:
        grapSty.append(doc.GetElement(i))
    for j in grapSty:
        grapStyCate.append(j.GraphicsStyleCategory.Name)
    return grapStyCate

#Select CAD file
fileCAD = SelectElemnt()
#Get import instance
instanceGeos = getInstanceGeometry(fileCAD)
#Get line from CAD file
line_lst = getLineFromGeoIns(instanceGeos)
#Get If of layers of CAD
graphic_id = getGraphicsStyleId(line_lst)
#Get layers of CAD
graphics_cate = getGraphicStyleCategory(graphic_id)

#A dictionary contains layer, Id of layer
dict_graphicsstyle = {cate:Id for cate, Id in zip(graphics_cate,graphic_id)}

#A form for users select layer
layers_CAD = forms.SelectFromList.show(
            dict_graphicsstyle.keys(),
            multiselect=True,
            title='Select layers',
            button_name='Select layers'
            )
#Get the Id of the selected layer
Id_Layer = dict_graphicsstyle[layers_CAD[0]]
#A dictionary contains line from layers, Id of layer
dict_line = {line:Id for line, Id in zip(line_lst,graphic_id)}

#Get line from selected layer
linefromlayer = [line for line, value in dict_line.items() if value == Id_Layer]

#Create grid from line
with Transaction(doc) as t:
    t.Start('Create grid')
    for line in linefromlayer:
        grid = Autodesk.Revit.DB.Grid.Create(doc, line)
        print (grid)
    t.Commit()
