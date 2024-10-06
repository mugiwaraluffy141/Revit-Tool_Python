'''
Function: Copy/Paste Filters in Current Model
-----------------------------------------------------------------
User Manual:
_ Step 1: Select the Source View containing Filters
_ Step 2: Select Filters that you want to Copy from Source View
_ Step 3: Select Target Views that you want to Paste Filters
-----------------------------------------------------------------
'''

import clr 
from pyrevit import forms
from rpw.ui.forms import Alert


clr.AddReference('RevitAPI')
import Autodesk
from Autodesk.Revit.DB import *

clr.AddReference('RevitAPIUI')
from  Autodesk.Revit.UI.Selection import*

doc = __revit__.ActiveUIDocument.Document
view = doc.ActiveView
uidoc = __revit__.ActiveUIDocument
app = __revit__.Application

#------------------------Select Source View to get Filter--------------------
#Create lists of wanted views
all_views = FilteredElementCollector(doc).OfCategory(BuiltInCategory.OST_Views).WhereElementIsNotElementType().ToElements()
template_views = [view for view in all_views if view.IsTemplate]
non_template_views = [view for view in all_views if view.IsTemplate == False]
filterviews_type = [str(view.ViewType) for view in non_template_views]

def GroupByKey(items,keys):
    #Create unique keys list
    unique_keys = []
    for key in keys:
        if key not in unique_keys:
            unique_keys.append(key)
    #Create empty list according to unique keys
    group_lst = []
    for key in unique_keys:
        group_lst.append([])
    #Get index of unique keys in the input key list
    index_lst = []
    for key in keys:
        index_lst.append(unique_keys.index(key))
    #Group by key
    for item, ind in zip(items,index_lst):
        group_lst[ind].append(item)
    
    return group_lst,unique_keys

def Flatten_LV3(lst):
    result = []
    for i in lst:
        for j in i:
            result.append(j)
    return result


#-----------------------------Main Logic----------------------------------------
#Group non-template views by their types
group_views = GroupByKey(non_template_views,filterviews_type)

#Create a dictionary containing non template views
non_template_dict = dict(zip(group_views[1],group_views[0]))

#Create a dictionary containing views have filters
all_views_dict = {i.Name:i for i in all_views}

#Create a dictionary contaning view templates have filters
template_views_dict = {i.Name:i for i in template_views}

#Form: Select Source View to get Filter
source_views_opt = {'All': sorted(all_views_dict),\
                    'View Template': sorted(template_views_dict)
                    }
source_views_opt.update({key:[i.Name for i in value] for key,value in non_template_dict.items()})
selected_source_view_name = forms.SelectFromList.show(source_views_opt,
                                multiselect=False,
                                group_selector_title='Source Views',
                                button_name='Select Source View')
if not selected_source_view_name:
    Alert('No Source View Selected. Please Select Again.',exit = True)


#------------------------Select Filters from Source View----------------------
#Form: Select Filters from Source View
source_view = all_views_dict.get(selected_source_view_name)

source_filter_Ids = source_view.GetFilters()

source_filters = [doc.GetElement(Id) for Id in source_filter_Ids]
source_filters_dict = {filter.Name:filter for filter in source_filters}


selected_source_filter_name = forms.SelectFromList.show({'Filters' : source_filters_dict},
                                multiselect=True,
                                group_selector_title='Filter Sets',
                                button_name='Select Filters to Copy')
if not selected_source_filter_name:
    Alert('No Source Filter Selected. Please Select Again.',exit = True)

#Get source filters from selected filter names
source_filters = [source_filters_dict.get(filter_name) for filter_name in selected_source_filter_name]
source_filter_Ids = [filter.Id for filter in source_filters]
filters_status = [source_view.GetFilterVisibility(Id) for Id in source_filter_Ids]


#-----------------------------Select target views-------------------------------
#Form: Select target views
target_views_opt = {'All': sorted(all_views_dict),\
                    'View Template': sorted(template_views_dict)
                    }
target_views_opt.update({key:[i.Name for i in value] for key,value in non_template_dict.items()})
selected_target_view_name = forms.SelectFromList.show(target_views_opt,
                                multiselect=True,
                                group_selector_title='Target Views',
                                button_name='Select Target Views')
if not selected_target_view_name:
    Alert('No Target View Selected. Please Select Again.',exit = True)

target_views = [all_views_dict.get(view_name) for view_name in selected_target_view_name]


#-----------------------Paste source filters to target views--------------------
t = Transaction(doc,'Copy Filters in Current Model')
t.Start()
for filter,status in zip(source_filters,filters_status):
    filter_overide = source_view.GetFilterOverrides(filter.Id)
    for view in target_views:
        try:
            view.SetFilterVisibility(filter.Id,status)
            view.SetFilterOverrides(filter.Id,filter_overide)
        except:
            pass
print ('Paste Filters Successfully')
t.Commit()
