'''
Function: Copy/Paste Filters from Linked Model
-----------------------------------------------------------------
User Manual:
_ Step 1: Select the Linked Model
_ Step 2: Select the Source View containing Filters
_ Step 3: Select Filters that you want to Copy from Source View
_ Step 4: Select Target Views that you want to Paste Filters
-----------------------------------------------------------------
'''

import clr 
from pyrevit import forms,script
from rpw.ui.forms import Alert
from System.Collections.Generic import *

clr.AddReference('RevitAPI')
import Autodesk
from Autodesk.Revit.DB import *

doc = __revit__.ActiveUIDocument.Document
view = doc.ActiveView
uidoc = __revit__.ActiveUIDocument
app = __revit__.Application
output = script.get_output()
#-------------------------------------------------------------------------------
def GetLinkDoc():
    linkInstances = FilteredElementCollector(doc).OfClass(RevitLinkInstance)
    linkDoc = []
    linkName = []
    for i in linkInstances:
        linkDoc.append(i.GetLinkDocument())
        linkName.append(i.Name)
    return linkDoc,linkName

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
all_link_doc = GetLinkDoc()

#---------------------------Select Linked Model----------------------------
all_link_doc_dict = dict(zip(all_link_doc[1],all_link_doc[0]))
selected_link_model_name = forms.SelectFromList.show({'Link Models' : sorted(all_link_doc_dict)},
                                multiselect=False,
                                group_selector_title='Link Model Sets',
                                button_name='Select a Link Model')
if not selected_link_model_name:
    Alert('No Linked Model Selected. Please Select Again.',exit = True)

selected_link_doc = all_link_doc_dict.get(selected_link_model_name)

#---------------------------Get View in Linked Model----------------------------
#Create lists of wanted views from Selected Linked Model
all_views = FilteredElementCollector(selected_link_doc).OfCategory(BuiltInCategory.OST_Views).WhereElementIsNotElementType().ToElements()
filter_views = [view for view in all_views if view.GetFilters()]
template_views = [view for view in filter_views if view.IsTemplate]
non_template_views = [view for view in filter_views if view.IsTemplate == False]
filterviews_type = [str(view.ViewType) for view in non_template_views]
#Group non-template views by their types
group_views = GroupByKey(non_template_views,filterviews_type)
#Create a dictionary containing non template views
non_template_dict = dict(zip(group_views[1],group_views[0]))
#Create a dictionary containing views have filters
filter_views_dict = {i.Name:i for i in filter_views}
#Create a dictionary contaning view templates have filters
template_views_dict = {i.Name:i for i in template_views}

#----------------------------Select Source View---------------------------------
#Form: Select Source View to get Filter
source_views_opt = {'All': sorted(filter_views_dict),\
                    'View Template': sorted(template_views_dict)
                    }
source_views_opt.update({key:[i.Name for i in value] for key,value in non_template_dict.items()})
selected_source_view_name = forms.SelectFromList.show(source_views_opt,
                                multiselect=False,
                                group_selector_title='Source Views',
                                button_name='Select Source View')
if not selected_source_view_name:
    Alert('No Source View Selected. Please Select Again.',exit = True)

#---------------------------Select Filter from Source View----------------------
#Form: Select Filters from Source View
source_view = filter_views_dict.get(selected_source_view_name)
source_filter_Ids = source_view.GetFilters()
source_filters = [selected_link_doc.GetElement(Id) for Id in source_filter_Ids]
source_filters_dict = {filter.Name:filter for filter in source_filters}
selected_source_filter_name = forms.SelectFromList.show({'Filters' : sorted(source_filters_dict)},
                                multiselect=True,
                                group_selector_title='Filter Sets',
                                button_name='Select Filters to Copy')
if not (selected_source_filter_name):
    Alert('No Source Filter Selected. Please Select Again.',exit = True)

#Get source filters from selected filter names
source_filters = [source_filters_dict.get(filter_name) for filter_name in selected_source_filter_name]
source_filter_Ids = [filter.Id for filter in source_filters]
source_filter_names = [filter.Name for filter in source_filters]
filters_status = [source_view.GetFilterVisibility(Id) for Id in source_filter_Ids]


#---------------------------Select Target View----------------------------------
#All View in current model
all_views_currentdoc = FilteredElementCollector(doc).OfCategory(BuiltInCategory.OST_Views).WhereElementIsNotElementType().ToElements()
all_views_currentdoc_dict = {i.Name:i for i in all_views_currentdoc}

#All view template in current model
template_views_currentdoc = [view for view in all_views_currentdoc if view.IsTemplate]
template_views_currentdoc_dict = {i.Name for i in template_views_currentdoc}

#Non-template view in current model
non_template_views_currentdoc = [view for view in all_views_currentdoc if view.IsTemplate == False]
non_template_views_currentdoc_type = [str(view.ViewType) for view in non_template_views_currentdoc]
group_non_template_views_currentdoc = GroupByKey(non_template_views_currentdoc,non_template_views_currentdoc_type)
groupbytype_non_template_views_currentdoc_dict = dict(zip(group_non_template_views_currentdoc[1],group_non_template_views_currentdoc[0]))
non_template_views_currentdoc_dict = {i.Name:i for i in non_template_views_currentdoc}

#Form: Select target views
target_views_opt = {'All' : sorted(all_views_currentdoc_dict),
                    'View Template' : sorted(template_views_currentdoc_dict)
                    }
target_views_opt.update({key:[i.Name for i in value] for key,value in groupbytype_non_template_views_currentdoc_dict.items()})
selected_target_view_name = forms.SelectFromList.show(target_views_opt,
                                multiselect=True,
                                group_selector_title='Target Views',
                                button_name='Select Target Views')
if not (selected_target_view_name):
    Alert('No Target View Selected. Please Select Again.',exit = True)

target_views = [all_views_currentdoc_dict.get(view_name) for view_name in selected_target_view_name]

# print (source_filter_names)
# print (filters_status)

#---------------------------Copy/Paste Filters----------------------------------
t = Transaction(doc,'Copy Filters from Linked Model')
t.Start()
# for filter in source_filters:
for filter,status in zip(source_filters,filters_status):

    #Create similar filters with the source filters in the current model
    name_filter = filter.Name #Get name of source filter
    categories_filter_Id = List[ElementId](filter.GetCategories()) #Get ID of categories and put in a ICollection(ElementId)
    rule_filter = filter.GetElementFilter() #Get the filter rules
    try:
        new_filter = ParameterFilterElement.Create(doc,name_filter,categories_filter_Id,rule_filter) #Create similar filter
    except:
        pass


    #Get filter override from source filter
    filter_overide = source_view.GetFilterOverrides(filter.Id)


    #Set filter override to current view
    for view in target_views:
        try:
            view.SetFilterVisibility(new_filter.Id,status)
            view.SetFilterOverrides(new_filter.Id,filter_overide)
        except:
            pass
print ('Paste Filters Successfully')
t.Commit()
