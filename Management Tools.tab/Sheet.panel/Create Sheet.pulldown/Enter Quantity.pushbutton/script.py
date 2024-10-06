'''
Function: Create Sheets according to Quantity of input
-----------------------------------------------------------------
User Manual:
_ Step 1: Select Title Block
_ Step 2: Enter the quantity of sheets that you want to create
-----------------------------------------------------------------
'''

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

#---------------------------Enter the Quantity of Sheet----------------------------------------
quantity_sheet = forms.ask_for_string(
    default='1',
    prompt='Enter the number of Sheet:',
    title='Quantity of Sheet'
)

#---------------------------Create Sheets----------------------------------------
tg = TransactionGroup(doc,'Create Sheets from Quantity')
tg.Start()
for i in range(0,int(quantity_sheet)):
	t=Transaction(doc,'Create Sheets')
	t.Start()
	new_sheet = ViewSheet.Create(doc,titleblock_Id)
	t.Commit()
print('There are {} Sheets have been created.'.format(quantity_sheet))
tg.Assimilate()
