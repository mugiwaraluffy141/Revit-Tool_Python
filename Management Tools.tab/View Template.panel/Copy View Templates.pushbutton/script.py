'''
Function: Copy/Paste View Templates from Linked Model.
-----------------------------------------------------------------
User Manual:
_ Step 1: Select Linked Model
_ Step 2: Select Target View Templates
-----------------------------------------------------------------
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
#---------------------------------------------------------------------------
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

#------------------------Get View Templates in Linked Model---------------------
#Form: Select A Linked Model
all_link_doc = GetLinkDoc()
all_link_doc_dict = dict(zip(all_link_doc[1],all_link_doc[0]))
selected_link_model_name = forms.SelectFromList.show({'Link Models' : sorted(all_link_doc_dict)},
                                multiselect=False,
                                group_selector_title='Link Model Sets',
                                button_name='Select a Link Model')
if not selected_link_model_name:
    Alert('No Linked Model Selected. Please Select Again.',exit = True)
selected_link_doc = all_link_doc_dict.get(selected_link_model_name)
all_linkviews = FilteredElementCollector(selected_link_doc).OfClass(View).WhereElementIsNotElementType().ToElements()
all_linkviewtemplates = [view for view in all_linkviews if view.IsTemplate]
all_linkviewtemplates_dict = {viewtemplate.Name : viewtemplate for viewtemplate in all_linkviewtemplates}

#Group by type
viewtemplates_type = [str(view.ViewType) for view in all_linkviewtemplates]
group_viewtemplate_type = GroupByKey(all_linkviewtemplates,viewtemplates_type)
viewtemplate_type_dict = dict(zip(group_viewtemplate_type[1],group_viewtemplate_type[0]))

#------------------------Select Target View Templates---------------------------
opt = {'All' : sorted(all_linkviewtemplates_dict)}
opt.update({key : [i.Name for i in value] for key,value in viewtemplate_type_dict.items()})
selected_viewtemplates_name = forms.SelectFromList.show(
    opt,
    multiselect=True,
    group_selector_title = 'View Templates',
    button_name = 'Select Target View Templates'                                                 
    )
if not selected_viewtemplates_name:
    Alert('No View Template Selected. Please Select Again.',exit = True)
selected_viewtemplate = [all_linkviewtemplates_dict.get(viewname) for viewname in selected_viewtemplates_name]

#------------------------Copy View Templates------------------------------------
viewtemplate_Id = List[ElementId]([i.Id for i in selected_viewtemplate])

with Transaction (doc,'Copy View Templates from Linked Model') as t:
    t.Start()

    ElementTransformUtils.CopyElements(selected_link_doc,viewtemplate_Id,doc,None,None)

    t.Commit()

#------------------------Print Result-------------------------------------------
print ('Copy View Templates Successfully.')
count = len(selected_viewtemplate)
if count > 1:
    print ('There are {} View Templates have been copied: '.format(count))
else:
    print ('There is 1 View Template has been copied: ')
for name in selected_viewtemplates_name:
    print (name)
