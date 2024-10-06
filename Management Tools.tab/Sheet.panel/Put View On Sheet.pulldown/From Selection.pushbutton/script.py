'''
Function: Place Views On Sheets from CSV
-----------------------------------------------------------------
User Manual:
_ Step 1: Select Template Sheet
_ Step 2: Select View from Template Sheet
_ Step 3: Select Target Sheets
_ Step 4: Select Target Views
-----------------------------------------------------------------
***Attention:
_ The order of Views and Sheets must correspond to each other
_ The tool only works with FloorPlan, Section, 3D, Legend, Schedule
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
allviews = FilteredElementCollector(doc).OfClass(View).WhereElementIsNotElementType().ToElements()
allsheets = [view for view in allviews if view.GetType() == DB.ViewSheet]
# allsheets_dict = {sheet.Number : sheet for sheet in allsheets}
sheetnumbers = [sheet.LookupParameter('Sheet Number').AsString() for sheet in allsheets]
sheets_dict = dict(zip(sheetnumbers,allsheets))

#Form: Select Template Sheet
selected_templatesheet_name = forms.SelectFromList.show({'All': sorted(sheets_dict)},
                                multiselect=False,
                                group_selector_title='Template Sheets',
                                button_name='Select A Template Sheet')
if not selected_templatesheet_name:
    Alert('No Template Sheet Selected. Please Select Again.',exit = True)
template_sheet = sheets_dict.get(selected_templatesheet_name)

#-------------------------Select View from Template Sheet-----------------------
#Get views on sheet and correspond view ports
views_on_sheet = [doc.GetElement(id) for id in template_sheet.GetAllPlacedViews()]
viewnames_on_sheet = [doc.GetElement(id).Name for id in template_sheet.GetAllPlacedViews()]
viewports_on_sheet = [doc.GetElement(id) for id in template_sheet.GetAllViewports()]

view_of_viewport = []
for viewport in viewports_on_sheet:
    view_of_viewport.append(doc.GetElement(viewport.ViewId).Name)

#Create views and viewports dictionaries
views_dict = {view.Name : view for view in views_on_sheet}
viewports_dict = dict(zip(view_of_viewport,viewports_on_sheet))

#Form: Select View from Template Sheet
selected_view_name = forms.SelectFromList.show({'All': sorted(views_dict)},
                                multiselect=False,
                                group_selector_title='Template Views',
                                button_name='Select A Template View')
if not selected_view_name:
    Alert('No Template View Selected. Please Select Again.',exit = True)
template_view = views_dict.get(selected_view_name)
templateview_location = viewports_dict.get(selected_view_name).GetBoxCenter()

#----------------------------Select Target Sheets--------------------------------
selected_targetsheet_name = forms.SelectFromList.show({'All': sorted(sheets_dict)},
                                multiselect=True,
                                group_selector_title='Target Sheets',
                                button_name='Select Target Sheets')
if not selected_targetsheet_name:
    Alert('No Target Sheet Selected. Please Select Again.',exit = True)
target_sheets = [sheets_dict.get(name) for name in selected_targetsheet_name]

#----------------------------Select Target Views--------------------------------
def GetValidViews(views):
    floorplan_views = []
    section_views = []
    threeD_views = []
    legend_views = []
    schedule_views = []
    for view in views:
        if view.IsTemplate == False:
            if view.ViewType == ViewType.FloorPlan:
                floorplan_views.append(view)
            elif view.ViewType == ViewType.Section:
                section_views.append(view)
            elif view.ViewType == ViewType.ThreeD:
                threeD_views.append(view)
            elif view.ViewType == ViewType.Legend:
                legend_views.append(view)
            elif view.ViewType == ViewType.Schedule:
                if 'Revision' not in view.Name:
                    schedule_views.append(view)
        
    return floorplan_views, section_views, threeD_views, legend_views, schedule_views

def Flatten_LV3(lst):
    result = []
    for i in lst:
        for j in i:
            result.append(j)
    return result

#Form: Select Target Views
valid_views = GetValidViews(allviews)
valid_views_dict = {view.Name : view for view in Flatten_LV3(valid_views)}
floorplan_dict = {view.Name : view for view in valid_views[0]}
section_dict = {view.Name : view for view in valid_views[1]}
threeD_dict = {view.Name : view for view in valid_views[2]}
lengend_dict = {view.Name : view for view in valid_views[3]}
schedule_dict = {view.Name : view for view in valid_views[4]}
target_opt = {
            'FloorPlan' : sorted(floorplan_dict),
            'Section' : sorted(section_dict),
            'ThreeD' : sorted(threeD_dict),
            'Legend' : sorted(lengend_dict),
            'Schedule' : sorted(schedule_dict)
              }

selected_targetview_names = forms.SelectFromList.show(target_opt,
                                multiselect=True,
                                group_selector_title='Target Views',
                                button_name='Select Target Views')
if not selected_targetview_names:
    Alert('No Target View Selected. Please Select Again.',exit = True)
target_views = [valid_views_dict.get(name) for name in selected_targetview_names]

#----------------------------Place Views on Sheets------------------------------
tg = TransactionGroup(doc,'Place Views On Sheets')
tg.Start()

if len(target_views) == 1:
    t = Transaction(doc,'Place Views On Sheets')
    t.Start()

    for sheet in target_sheets:
        Viewport.Create(doc,sheet.Id,target_views[0].Id,templateview_location)

    t.Commit()
elif len(target_views) > 1:
    t = Transaction(doc,'Place Views On Sheets')
    t.Start()

    for sheet,view in zip(target_sheets,target_views):
        Viewport.Create(doc,sheet.Id,view.Id,templateview_location)

    t.Commit()
print ('Place Views On Sheets Successfully.')
tg.Assimilate()

