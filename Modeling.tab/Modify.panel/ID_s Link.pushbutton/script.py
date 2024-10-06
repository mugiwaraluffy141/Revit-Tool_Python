'''
Function: Get the ID of linked elements
'''
from Autodesk.Revit.UI.Selection import ObjectType

#get UIdocment and document
uidoc = __revit__.ActiveUIDocument

pick = uidoc.Selection.PickObjects(ObjectType.LinkedElement)
link_Id = [i.LinkedElementId for i in pick]
print(','.join(str(Id) for Id in link_Id))