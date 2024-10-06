import clr 
import math
import xlsxwriter
import os
from collections import OrderedDict


clr.AddReference('RevitAPI')
import Autodesk
from Autodesk.Revit.DB import *

clr.AddReference('RevitAPIUI')
from  Autodesk.Revit.UI.Selection import*

doc = __revit__.ActiveUIDocument.Document
view = doc.ActiveView
uidoc = __revit__.ActiveUIDocument
app = __revit__.Application
#---------------------------------------------------------
#Select elments by category
class selectionfilter(ISelectionFilter):
    def __init__(self,category1,category2):
        self.category1 = category1
        self.category2 = category2

    def AllowElement(self, element):
        if element.Category.Name == self.category1 or element.Category.Name == self.category2:
            return True
        else:
            return False
    
    def AllowReference(self,point): #It's not neccessary to use this definition
        return False
select_ele = selectionfilter('NOT','Floors')
familyinstances = uidoc.Selection.PickElementsByRectangle(select_ele,'Select')
ele = [doc.GetElement(i.Id) for i in familyinstances]

#Get value of parameter
def get_param_value(param):
    value = None
    DB = Autodesk.Revit.DB
    if isinstance(param, DB.Parameter):
        if param.StorageType == DB.StorageType.Double:
            value = math.ceil(param.AsDouble()*304.8)
        elif param.StorageType == DB.StorageType.Integer:
            value = param.AsInteger()
        elif param.StorageType == DB.StorageType.String:
            value = param.AsString()
        elif param.StorageType == DB.StorageType.ElementId:
            value = param.AsElementId()
    elif isinstance(param, DB.GlobalParameter):
        return param.GetValue().Value
    return value

#Get type parameter of element
def get_param_by_name(elements,name):
    getFamilyType = [doc.GetElement(i.GetTypeId()) for i in elements]
    params = [i.LookupParameter(name) for i in getFamilyType]
    var = [get_param_value(i) for i in params]
    return var
#
ids = [i.Id.IntegerValue for i in familyinstances]
names = [i.Name for i in ele]
thickness_param = get_param_by_name(familyinstances,'Default Thickness')

# 1 ft^3 = 0.02831 m^3
volume_param = [i.get_Parameter(BuiltInParameter.HOST_VOLUME_COMPUTED).AsDouble()*0.02831 for i in ele]

path = 'C:\\Users\\PC\\Desktop\\New Microsoft Excel Worksheet.xlsx'

#Open the Excel file to write data in
workbook = xlsxwriter.Workbook(path)
worksheet = workbook.add_worksheet()

#Use OrderedDict to maintainn the order of data in Excel like in the dictionary 
my_dict = OrderedDict([
    ('Id', ids),
    ('Name', names),
    ('Thickness', thickness_param),
    ('Volume', volume_param)
])

#Write data in Excel
col_num = 0
for key, value in my_dict.items():
    worksheet.write(0, col_num, key)
    worksheet.write_column(1, col_num, value)
    col_num += 1
workbook.close()

#Open the file after export
os.startfile(path)
