'''
Function: Check elements haven't tagged in view
User manual: Select categories to check
'''
import clr 
from pyrevit import revit,forms,script
from rpw.ui.forms import Alert


clr.AddReference('RevitAPI')
import Autodesk
from Autodesk.Revit.DB import *


doc = __revit__.ActiveUIDocument.Document
view = doc.ActiveView
uidoc = __revit__.ActiveUIDocument
app = __revit__.Application
DB = Autodesk.Revit.DB
output = script.get_output()
unit = doc.GetUnits()
version = int(app.VersionNumber)
#--------------------------------------Fuction--------------------------------------------------------------------------   
def ToList(ele):
    if isinstance(ele,list):
        return ele
    else:
        return [ele]

def Flatten_lv3 (lst):
    return [i for sub_lst in lst for i in sub_lst]

def AllElementOfCategoryInView(categoryName):
	categoryName = ToList(categoryName)
	allCategories = doc.Settings.Categories
	valid_cate = []
	alleles = []
	for cate in allCategories:
		for category in categoryName:
			if cate.Name == category:
				valid_cate.append(cate)

	for cate in valid_cate:
		alleles.append(FilteredElementCollector(doc,view.Id).OfCategoryId(cate.Id).WhereElementIsNotElementType().ToElements())

	return Flatten_lv3(alleles)

def AllAnnotationCategory():
    allCategories = doc.Settings.Categories
    result = []
    for category in allCategories:
        if category.CategoryType == CategoryType.Annotation:
            result.append(category)
    return result

def SetDifference(lst1, lst2): #lst 1 > lst2
    result = []
    for item1 in lst1:
        if item1 not in lst2:
            result.append(item1)
    return result

def GroupByKey(items,keys):
    #Create unique key lists
    unique_keys = []
    for key in keys:
        if key not in unique_keys:
            unique_keys.append(key)
    
    #Create empty lists according to unique keys
    group_lst = []
    for i in range(len(unique_keys)):
        group_lst.append([])
    
    #Get index of the input keys in unique key lists
    ind_lst = []
    for key in keys:
        ind_lst.append(unique_keys.index(key))
    
    #Group by key
    for item, ind in zip(items,ind_lst):
        group_lst[ind].append(item)
    
    return group_lst,unique_keys

def GetTaggedElement(tag):
    result = []
    if version < 2022:
        taggedElement = tag.GetTaggedLocalElement()
        result.append(taggedElement)
    else:
        taggedElements = tag.GetTaggedLocalElements()
        for element in taggedElements:
            result.append(element)
    return result

def GetElementCategory(ele):
    return ele.Category.Name

def GetFamilyNameOfElement(ele):
    return ele.LookupParameter('Family').AsValueString()

def GetTypeNameOfElement(ele):
    return ele.Name
#--------------------------------------Main Logic-----------------------------------------------------------------------
annotationCate = AllAnnotationCategory()
annotationCateName = [cate.Name for cate in annotationCate]
annotaionCateDict = dict(zip(annotationCateName,annotationCate))

#Select form
selectCateName = forms.SelectFromList.show(
        {'Annotation Categories' : sorted(annotaionCateDict)},
        title='MultiGroup List',
        group_selector_title='Select Categories',
        multiselect=True
    )

if not selectCateName:
    Alert('No Category Selected. Please Select Again',exit = True)

#Get tagged elements and model elements
allTagOfCateInView = AllElementOfCategoryInView(selectCateName)
taggedElement = Flatten_lv3([GetTaggedElement(tag) for tag in allTagOfCateInView])           #List 2

cateNameOfTaggedElement = sorted(list(set([ele.Category.Name for ele in taggedElement])))
allModelElement = AllElementOfCategoryInView(cateNameOfTaggedElement)                 #List 1


#---------------------------------Compare and find elements have not been tagged----------------------------------------
taggedElementId = [element.Id for element in taggedElement]
modelElementId = [element.Id for element in allModelElement]

notTaggedElementId = SetDifference(modelElementId,taggedElementId)
notTaggedCategory = [doc.GetElement(Id).Category.Name for Id in notTaggedElementId]

groupElementByCategory = GroupByKey(notTaggedElementId,notTaggedCategory)
elementGroup = groupElementByCategory[0]    #Get elements have been grouped
cateGroup = groupElementByCategory[1]

taggedCategory = list(set(cateNameOfTaggedElement) - set(cateGroup))
if len(taggedCategory) != 0:
    taggedCategory_string = ", ".join(map(str, taggedCategory))
    print ('All Elements Of  {} Have Been Tagged.'.format(taggedCategory_string))

if len(allTagOfCateInView) == 0:
    Alert('All Elements Have Not Been Tagged.',exit = True)
else:
    if len(cateGroup) != 0:
        notTaggedCategory = [GetElementCategory(doc.GetElement(Id)) for Id in notTaggedElementId]
        notTaggedFamily = [GetFamilyNameOfElement(doc.GetElement(Id)) for Id in notTaggedElementId]
        notTaggedType = [GetTypeNameOfElement(doc.GetElement(Id)) for Id in notTaggedElementId]
        IdLinkify = [output.linkify(Id) for Id in notTaggedElementId]

        data = list(zip(notTaggedCategory,notTaggedFamily,notTaggedType,IdLinkify))
        output.print_table(table_data=data,
                        title  ='Result',
                        columns=['Category', 'Family', 'Type', 'Id'],
                        formats=['', '', '',''])
