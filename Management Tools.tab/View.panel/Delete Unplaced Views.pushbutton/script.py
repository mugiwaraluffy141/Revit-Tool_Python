'''
Function: Delete FloorPlan, DraftingView, Section, 3D, Schedule, Legend, Elevation not in Sheet.
-----------------------------------------------------------------
User Manual: 
Just press the button to run
-----------------------------------------------------------------
'''
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
#-------------------------------------------------------------
all_sheets = FilteredElementCollector(doc).OfCategory(BuiltInCategory.OST_Sheets).WhereElementIsNotElementType().ToElements()

view_on_sheets = []
for sheet in all_sheets:
    placed_views = sheet.GetAllPlacedViews()
    for view_id in placed_views:
        view_on_sheets.append(view_id)

all_views = FilteredElementCollector(doc).OfCategory(BuiltInCategory.OST_Views).WhereElementIsNotElementType().ToElements()
valid_view = []
for view in all_views:
    if not view.IsTemplate and view.ViewType in [ViewType.FloorPlan, ViewType.DraftingView, ViewType.Section, ViewType.ThreeD, ViewType.Schedule, ViewType.Legend, ViewType.Elevation]:
        valid_view.append(view.Id)
      
result = []
for j in valid_view:
    if j not in view_on_sheets:
        result.append(j)

with TransactionGroup(doc, 'Delete Unused Views') as tg:
    tg.Start()
    with Transaction(doc, 'Delete Unused Views') as t:
        t.Start()
        for Id in result:
            view_dependent = doc.GetElement(Id).GetDependentViewIds()
            if len(view_dependent) == 0:
                try:
                    doc.Delete(Id)
                except:
                    pass                   
        t.Commit()
    print('Done')
    tg.Assimilate()
