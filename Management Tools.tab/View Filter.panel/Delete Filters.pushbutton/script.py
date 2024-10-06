'''
Function: Delete Selected Filters
-----------------------------------------------------------------
User Manual:
_ Step 1: Select Filters
_ Step 2: Press 'Delete Filters' button
-----------------------------------------------------------------
'''
#!/usr/bin/env python
# -*- coding: utf-8 -*-

import clr 
from pyrevit import revit,forms,script
from rpw.ui.forms import Alert


clr.AddReference('RevitAPI')
import Autodesk
from Autodesk.Revit.DB import *


doc = __revit__.ActiveUIDocument.Document
view = doc.ActiveView
uidoc = __revit__.ActiveUIDocument
app = __revit__.Application
DB = Autodesk.Revit.DB
output = script.get_output()


#----------------------------------Main Logic---------------------------------------------------------------------------
allViewFilter = FilteredElementCollector(doc).OfClass(ParameterFilterElement).WhereElementIsNotElementType().ToElements()
filterName = [filter.Name for filter in allViewFilter]
filterDict = dict(zip(filterName,allViewFilter))
selectedFilterName = forms.SelectFromList.show({'Filters' : sorted(filterDict)},
                                multiselect=True,
                                group_selector_title='Filter Sets',
                                button_name='Delete Filters')
if not selectedFilterName:
    Alert('No Filter Selected. Please Select Again.',exit = True)


#--------------------------------Delete Filters-------------------------------------------------------------------------
with Transaction(doc,'Delete Filters') as t:
    t.Start()
    result = []
    for name in selectedFilterName:
        id = filterDict.get(name).Id
        try:
            doc.Delete(id)
        except Exception as er:
            result.append(er)
    
    if len(result) == 0 :
        print ('Done')
    else:
        print (result)
    t.Commit()