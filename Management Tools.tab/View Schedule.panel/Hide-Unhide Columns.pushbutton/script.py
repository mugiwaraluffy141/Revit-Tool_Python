'''
Function: Hide/Unhide Columns in Schedules
-----------------------------------------------------------------
User Manual:
_ Step 1: Select Schedules
_ Step 2: Select Columns that you want to Hide/Unhide
_ Step 3: Select option to Hide or Unhide
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
#------------------------------------------------------------------------------
#Prepare input
def tolist(input):
    if isinstance(input,list):
        a = input
    else:
        a = [input]
    return a

def Uniqueitems(items):
    unique_item = []
    for item in items:
        if item not in unique_item:
            unique_item.append(item)
    return unique_item

#Step 1: Select Schedules
allviews = FilteredElementCollector(doc).OfClass(View).WhereElementIsNotElementType().ToElements()
allschedules = [view for view in allviews if view.GetType() == Autodesk.Revit.DB.ViewSchedule]
schedule_dict = {schedule.Name:schedule for schedule in allschedules}
selected_schedule_names = forms.SelectFromList.show({'All': sorted(schedule_dict)},
                                multiselect=True,
                                group_selector_title='Schedules Set',
                                button_name='Select Schedule')
if not selected_schedule_names:
    Alert('No Schedule Selected. Please Select Again.',exit = True)
get_selected_schedules = [schedule_dict.get(schedule_name) for schedule_name in selected_schedule_names] #get value at key

# Step 2: Select Columns
column_schedules = []
for schedule in get_selected_schedules:
    definit = schedule.Definition
    countParams = definit.GetFieldCount() 
    for i in range(countParams):
        param_name = definit.GetField(i).ColumnHeading
        column_schedules.append(param_name)
column_schedules = Uniqueitems(column_schedules)
selected_column_names = forms.SelectFromList.show({'All': column_schedules},
                                multiselect=True,
                                group_selector_title='All Columns',
                                button_name='Select Columns')
if not selected_column_names:
    Alert('No Column Selected. Please Select Again.',exit = True)
#Step 3: Select option to Hide or Unhide
selected_option = forms.CommandSwitchWindow.show(
    ['Hide', 'Unhide'],
    message='Select Option:',
)
if not selected_option:
    Alert('No Option Selected. Please Select Again.',exit = True)
elif selected_option == 'Hide':
    opt = True
else:
    opt = False

#Hide or Unhide Columns
tg = TransactionGroup(doc,'Hide/Unhide Column Schedules')
tg.Start()

def HideColumnSchedule(schedules,colName,opt):
    results = []
    for schedule in schedules:           
        definit = schedule.Definition
        countParameters = definit.GetFieldCount() 
        # Parameter names
        index = None
        for i in range(countParameters):
            Parname = definit.GetField(i).ColumnHeading  # Parameter Column name
            for name in colName:
                if Parname == name:
                    index = i
            if index is not None:
                field = schedule.Definition.GetField(index)  # schedule field
                            
                t = Transaction(doc,'Hide Column Schedule')
                t.Start()
                                
                field.IsHidden = opt
                                
                t.Commit()			
    return results

HideColumnSchedule(get_selected_schedules,selected_column_names,opt)

#Notification
if opt:
    print ('Hide Columns in Schedules Successfully')
else:
    print ('Unhide Columns in Schedules Successfully')

tg.Assimilate()