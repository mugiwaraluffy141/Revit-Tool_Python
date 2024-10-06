#!/usr/bin/env python
# -*- coding: utf-8 -*-
'''
Function: Add Fields To Schedules.
-----------------------------------------------------------------
User Manual:
_ Step 1: Select Schedules
_ Step 2: Select Fields
-----------------------------------------------------------------
'''
import clr 
from pyrevit import revit,forms,script
from rpw.ui.forms import Alert

clr.AddReference('RevitAPI')
import Autodesk
from Autodesk.Revit.DB import *

clr.AddReference('RevitAPIUI')
from  Autodesk.Revit.UI import TaskDialog

doc = __revit__.ActiveUIDocument.Document
view = doc.ActiveView
uidoc = __revit__.ActiveUIDocument
app = __revit__.Application
DB = Autodesk.Revit.DB
output = script.get_output()
version = app.VersionNumber
#----------------------------------Function-----------------------------------------------------------------------------
def tolst(ele):
    if isinstance(ele,list):
        return ele
    else:
        return [ele]

def flatten_lv3 (lst):
    return [i for sub_lst in lst for i in sub_lst]

def AllElementOfCategory(categories):
	categories = tolst(categories)
	allcates = doc.Settings.Categories
	valid_cate = []
	alleles = []
	for cate in allcates:
		for category in categories:
			if cate.Name == category:
				valid_cate.append(cate)

	for cate in valid_cate:
		alleles.append(FilteredElementCollector(doc).OfCategoryId(cate.Id).WhereElementIsNotElementType().ToElements())

	return flatten_lv3(alleles)

def GetAvailableFieldOfSchedule(schedule):
	fields = schedule.Definition.GetSchedulableFields()
	return fields

def AddFieldToSchedule(schedule,field):
    with Transaction(doc,'Add Field To Schedule') as t:
        t.Start()
        try:
            schedule.Definition.AddField(field)
        except:
            pass
        t.Commit()
#----------------------------------Main Logic---------------------------------------------------------------------------
# Select schedules
allSchedules = AllElementOfCategory('Schedules')
scheduleNames = [schedule.Name for schedule in allSchedules]
scheduleDict = dict(zip(scheduleNames,allSchedules))

selectedScheduleNames = forms.SelectFromList.show({'All Schedules' : sorted(scheduleDict)},
                                multiselect=True,
                                group_selector_title='Schedule Sets',
                                button_name='OK')
if not selectedScheduleNames:
    Alert('No Schedule Selected. Please Select Again.',exit = True)
selectedSchedules = [scheduleDict.get(name) for name in selectedScheduleNames]

# Select fields
availableFieldsSchedules = [GetAvailableFieldOfSchedule(schedule) for schedule in allSchedules]
availableFieldsIds = []
availableFieldsNames = []

for sublst in availableFieldsSchedules:
    tempLst1 = []
    tempLst2 = []
    for field in sublst:
        fieldId = field.ParameterId.IntegerValue
        fieldName = field.GetName(doc)
        tempLst1.append(fieldId)
        tempLst2.append(fieldName)
    availableFieldsIds.append(tempLst1)
    availableFieldsNames.append(tempLst2)

uniqueFieldIds = []
uniqueFieldNames = []
uniqueFields = []

for sublst1,sublst2,sublst3 in zip(availableFieldsIds,availableFieldsNames,availableFieldsSchedules):
    for Id,name,field in zip(sublst1,sublst2,sublst3):
        if Id not in uniqueFieldIds:
            uniqueFieldIds.append(Id)
            uniqueFieldNames.append(name)
            uniqueFields.append(field)
uniqueFieldDict = dict(zip(uniqueFieldNames,uniqueFields))

selectedFieldNames = forms.SelectFromList.show({'All Fields' : sorted(uniqueFieldDict)},
                                multiselect=True,
                                group_selector_title='Field Sets',
                                button_name='OK')
if not selectedFieldNames:
    Alert('No Field Selected. Please Select Again.',exit = True)
selectedFields = [uniqueFieldDict.get(name) for name in selectedFieldNames]
#----------------------------------Add Field---------------------------------------------------------------------------
with TransactionGroup(doc,'Add Fields To Schedules') as tg:
    tg.Start()
    for schedule in selectedSchedules:
        for field in selectedFields:
            AddFieldToSchedule(schedule,field) 
    TaskDialog.Show('Result','Add Fields To Schedules Successfully.')
    tg.Assimilate()