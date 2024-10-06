# -*- coding: utf-8 -*-
'''
Function: Place Views On Sheets from CSV
Note: Alt + Left Click to see the Sample file
-----------------------------------------------------------------
User Manual:
_ Step 1: Select CSV File
-----------------------------------------------------------------
***Attention: 
_ Template Sheet must always be the first sheet in CSV
'''
import csv
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
#---------------------------Get Data from CSV File----------------------------
#Form: Select Excel file
template_file = forms.pick_file(file_ext='csv')
if not template_file:
    Alert('No CSV File Selected. Please Select Again.',exit = True)
if template_file:
	with open(template_file,'r') as csvfile:
		file_content = []
		f =  csv.reader(csvfile)
		for i in f:
			file_content.append(i)

#Remove the title from Excel
modified_file = file_content[1:]

#-----------------------------------------------------------------------------
allviews = FilteredElementCollector(doc).OfClass(View).WhereElementIsNotElementType().ToElements()
allsheets = [view for view in allviews if view.GetType() == DB.ViewSheet]

template_sheet_number = modified_file[0][0]
template_sheet = [sheet for sheet in allsheets if sheet.LookupParameter('Sheet Number').AsString() == template_sheet_number][0]

viewports_on_sheet = [doc.GetElement(id) for id in template_sheet.GetAllViewports()]

#Get Target Sheets from CSV
sheet_from_CSV = []
for i in range(1,len(modified_file)):
	for sheet in allsheets:
		if sheet.LookupParameter('Sheet Number').AsString() == modified_file[i][0]:
			sheet_from_CSV.append(sheet)

#Get Target Views from CSV
view_from_CSV = []
for i in range(1,len(modified_file)):
	sub_lst = []
	for j in range(1,len(modified_file[i])):
		for view in allviews:
			if modified_file[i][j] == view.Name:
				sub_lst.append(view)
	view_from_CSV.append(sub_lst)

#Get location of template View according to CSV
templateview_location = []
template_viewport = []
for i in range(1,len(modified_file[0])):
	for viewport in viewports_on_sheet:
		if modified_file[0][i] == doc.GetElement(viewport.ViewId).Name:
			templateview_location.append(viewport.GetBoxCenter())
			template_viewport.append(viewport.GetTypeId())
templateview_location = [templateview_location]*len(sheet_from_CSV)
template_viewport = [template_viewport]*len(sheet_from_CSV)

# ----------------------------Place Views on Sheets-----------------------------
with TransactionGroup(doc, 'Place Views On Sheets') as tg:
	tg.Start()
	for sheet, view_lst, location_lst, viewport_lst in zip(sheet_from_CSV,view_from_CSV,templateview_location,template_viewport):
		for view, location, viewport in zip(view_lst,location_lst,viewport_lst):
			with Transaction(doc, 'Place Views On Sheets') as t:
				t.Start()
				Viewport.Create(doc,sheet.Id,view.Id,location).LookupParameter('Family and Type').Set(viewport)
				t.Commit()
	print ('Place View On Sheets Successfully.')	
	tg.Assimilate()



