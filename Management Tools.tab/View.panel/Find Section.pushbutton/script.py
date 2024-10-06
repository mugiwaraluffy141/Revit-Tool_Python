#!/usr/bin/env python
# -*- coding: utf-8 -*-
'''
Function: Find Selected Sections.
-----------------------------------------------------------------
User Manual:
Select Sections that you want to find
-----------------------------------------------------------------
'''
import clr 
from pyrevit import forms,script

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
#Get all sections in model
all_callouts = FilteredElementCollector(doc).OfCategory(BuiltInCategory.OST_Viewers).WhereElementIsNotElementType().ToElements()
all_sections = [ele for ele in all_callouts if ele.LookupParameter('Family').AsValueString() == 'Section']
section_names = [section.Name for section in all_sections]
# print (all_sections)

section_dict = dict(zip(section_names,all_sections))
# print (section_dict)

selected_section_name = forms.SelectFromList.show({'All Sections' : sorted(section_dict)},
                                multiselect=True,
                                group_selector_title='All Sections',
                                button_name='Select Section')

# print (selected_section_name)
for name in selected_section_name:
    print(name + " " + output.linkify(section_dict.get(name).Id))






