'''
Function: Delete Import CAD in the model.
-----------------------------------------------------------------
User Manual:
_ Step 1: Select Import CAD that you want to delete
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
#-------------------------------------------------------------------------------
import_instances = FilteredElementCollector(doc).OfClass(ImportInstance).WhereElementIsNotElementType().ToElements()
import_Id = [i.Category.Id for i in import_instances]
import_names = [doc.GetElement(i).Name for i in import_Id]
importCAD_dict = dict(zip(import_names,import_Id))
select_opt = {'All' : sorted(importCAD_dict)}
selected_importCAD_names = forms.SelectFromList.show({'All': sorted(importCAD_dict)},
                                multiselect=True,
                                group_selector_title='All Import CADs',
                                button_name='Select Import CAD')
if not selected_importCAD_names:
    Alert('No Imported CAD Selected. Please Select Again.',exit = True)
lst_Id = List[ElementId]([importCAD_dict.get(name) for name in selected_importCAD_names])

#-------------------------------------------------------------------------------
with Transaction(doc,'Delete Import CAD file') as t:
    t.Start()
    doc.Delete(lst_Id)
    print ('Delete Import CAD successfully.')
    t.Commit()

