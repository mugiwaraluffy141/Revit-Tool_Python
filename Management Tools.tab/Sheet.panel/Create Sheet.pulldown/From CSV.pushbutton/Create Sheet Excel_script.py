# -*- coding: utf-8 -*-
'''
Function: Create Sheets from CSV file
Note: Alt + Left Click to see the Sample file
-----------------------------------------------------------------
User Manual:
_ Step 1: Select the CSV file
_ Step 2: Select Title Block
-----------------------------------------------------------------
'''
import csv
import clr 
from pyrevit import forms
from rpw.ui.forms import Alert

clr.AddReference('RevitAPI')
import Autodesk
from Autodesk.Revit.DB import *

doc = __revit__.ActiveUIDocument.Document
view = doc.ActiveView
uidoc = __revit__.ActiveUIDocument
app = __revit__.Application
#---------------------------Get CSV File----------------------------------------
#Form: Select Excel file
source_file = forms.pick_file(file_ext='csv')
if not source_file:
    Alert('No CSV File Selected. Please Select Again.',exit = True)
if source_file:
	with open(source_file,'r') as csvfile:
		sheet_number = []
		sheet_name = []
		f = csv.reader(csvfile)
		for row in f:
			sheet_number.append(row[0])
			sheet_name.append(row[1])
#---------------------------Get All Title Blocks----------------------------------------
#Collect title blocks (include family symbol and family instance)
titleblock_collector = FilteredElementCollector(doc).OfCategory(BuiltInCategory.OST_TitleBlocks).ToElements()

#Filter to just to get the family symbol (family type)
all_titleblock = [titleblock for titleblock in titleblock_collector if isinstance (titleblock,Autodesk.Revit.DB.FamilySymbol)]

#Get type name of titleblock
all_typename = []
for type in all_titleblock:
	#Get the Family Type Name Parameter
	parameter = type.get_Parameter(BuiltInParameter.SYMBOL_NAME_PARAM)
	
	#Get the Value of the Parameter --> The Name
	typeName = parameter.AsString()
	
	#Add the Name to the Output List
	all_typename.append(typeName)

#Form: Select Title Blocks
type_dict =  dict(zip(all_typename,all_titleblock))
selected_titleblock_names = forms.SelectFromList.show({'All': sorted(type_dict)},
                                multiselect=False,
                                group_selector_title='Title Blocks Set',
                                button_name='Select Title Blocks')
if not selected_titleblock_names:
    Alert('No Title Block Selected. Please Select Again.',exit = True)
selected_titleblock = type_dict.get(selected_titleblock_names)
titleblock_Id = selected_titleblock.Id

#---------------------------Create Sheets----------------------------------------
tg = TransactionGroup(doc,'Create Sheets from Excel')
tg.Start()
for i in range(1,len(sheet_number)):
	t=Transaction(doc,'Create Sheets')
	t.Start()

	new_sheet = ViewSheet.Create(doc,titleblock_Id)
	new_sheet.LookupParameter('Sheet Number').Set(sheet_number[i]) #Set value for Sheet Number
	new_sheet.LookupParameter('Sheet Name').Set(sheet_name[i]) #Set value for Sheet Name

	t.Commit()
quantity = len(sheet_number)-1
if quantity > 1:
	print('There are {} Sheets have been created.'.format(quantity))
else:
	print('There is {} Sheet has been created.'.format(quantity))
tg.Assimilate()
