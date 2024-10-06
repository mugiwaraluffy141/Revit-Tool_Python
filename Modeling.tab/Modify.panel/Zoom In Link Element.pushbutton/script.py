from ast import Sub
import clr 
import math
import xlsxwriter
import os
import collections
from pyrevit import revit,forms,script
from pyrevit.forms import ProgressBar
from Autodesk.Revit.UI.Selection import ObjectType 
from System.Collections.Generic import *
from rpw.ui.forms import Alert

clr.AddReference('ProtoGeometry')
import Autodesk.DesignScript.Geometry as DSGeo
from Autodesk.DesignScript.Geometry import *

clr.AddReference('RevitAPI')
import Autodesk
from Autodesk.Revit.DB import *

clr.AddReference('RevitAPIUI')
from  Autodesk.Revit.UI import*
from  Autodesk.Revit.UI.Selection import*
from  Autodesk.Revit.UI.Selection import*


clr.AddReference('RevitServices')
import RevitServices
from RevitServices.Persistence import DocumentManager
from RevitServices.Transactions import TransactionManager

import System.Drawing
import System.Windows.Forms
import collections

from System.Drawing import *
from System.Windows.Forms import *

doc = __revit__.ActiveUIDocument.Document
view = doc.ActiveView
uidoc = __revit__.ActiveUIDocument
app = __revit__.Application
DB = Autodesk.Revit.DB
output = script.get_output()
unit = doc.GetUnits()
version = int(app.VersionNumber)
selection = uidoc.Selection

uiviews = uidoc.GetOpenUIViews()
uiview = [x for x in uiviews if x.ViewId == view.Id][0]

#-----------------------------Function------------------------------------------
def GetLinkDoc():
    linkInstances = FilteredElementCollector(doc).OfClass(RevitLinkInstance).ToElements()
    linkDoc = []
    linkName = []
    for i in linkInstances:
        linkDoc.append(i.GetLinkDocument())
        linkName.append(i.Name)
    return linkDoc,linkName,linkInstances


#-----------------------------Function------------------------------------------
allLinkDoc = GetLinkDoc()

#Select link file
allLinkDocDict = dict(zip(allLinkDoc[1],allLinkDoc[0]))
selectedLinkModelName = forms.SelectFromList.show({'Link Models' : sorted(allLinkDocDict)},
                                multiselect=False,
                                group_selector_title='Link Model Sets',
                                button_name='Select a Link Model')
if not selectedLinkModelName:
    Alert('No Linked Model Selected. Please Select Again.',exit = True)

# print (allLinkDoc[1])
# print (allLinkDoc[2])
for ind,name in enumerate(allLinkDoc[1]):
    if selectedLinkModelName == name:
        linkedRvtInstance = allLinkDoc[2][ind]


#Input link ID
linkID = forms.ask_for_string(
    default='Linked Element ID',
    prompt='Enter a linked element ID',
    title=None
)


selectedLinkDoc = allLinkDocDict.get(selectedLinkModelName)
linkElement = selectedLinkDoc.GetElement(ElementId(int(linkID)))
# print (linkElement)

# Zoom in selected space
reference = Reference(linkElement)


reference = reference.CreateLinkReference(linkedRvtInstance)


uidoc.Selection.SetReferences([reference])

bbx =  linkElement.get_BoundingBox(None)
pt1 = XYZ(bbx.Min.X, bbx.Min.Y, bbx.Min.Z)
pt2 = XYZ(bbx.Max.X, bbx.Max.Y, bbx.Max.Z)		
uiview.ZoomAndCenterRectangle(pt2, pt1)


# reference = Reference(linkElement)
# reference = reference.CreateLinkReference(linkedRvtInstance)
# uidoc.Selection.SetReferences([reference])