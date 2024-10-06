'''
Function: Convert Grids in active view.
-----------------------------------------------------------------
User Manual:
_ Step 1: Select an option to convert
-----------------------------------------------------------------
'''
import clr 
from pyrevit import forms
from System.Collections.Generic import *
from rpw.ui.forms import Alert

clr.AddReference('RevitAPI')
import Autodesk
from Autodesk.Revit.DB import *

doc = __revit__.ActiveUIDocument.Document
view = doc.ActiveView
uidoc = __revit__.ActiveUIDocument
app = __revit__.Application
DB = Autodesk.Revit.DB
#----------------------------Select Template Sheet------------------------------
grid_actveview = FilteredElementCollector(doc,view.Id).OfClass(Grid).WhereElementIsNotElementType().ToElements()

selected_option = forms.CommandSwitchWindow.show(
    ['3D to 2D', '2D to 3D'],
    message='Select Option:',
)
if not selected_option:
    Alert('No Option Selected. Please Select Again.',exit = True)
if selected_option == '3D to 2D':
    t = Transaction(doc,'Convert Grids')
    t.Start()

    for i in grid_actveview:
        i.SetDatumExtentType(DatumEnds.End0,view, DatumExtentType.ViewSpecific)
        i.SetDatumExtentType(DatumEnds.End1,view, DatumExtentType.ViewSpecific)

    t.Commit()
else:
    t = Transaction(doc,'Convert Grids')
    t.Start()

    for i in grid_actveview:
        i.SetDatumExtentType(DatumEnds.End0,view, DatumExtentType.Model)
        i.SetDatumExtentType(DatumEnds.End1,view, DatumExtentType.Model)

    t.Commit()

print ('Convert Grids Sucessfully')