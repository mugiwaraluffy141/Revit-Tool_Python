from ast import Sub
from Autodesk.Revit.DB.Structure import StructuralType
import clr 
import math
import xlsxwriter
import os
import collections
from pyrevit import revit,forms,script

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
#-----------------------------Function------------------------------------------
get_ref = uidoc.Selection.PickObject(ObjectType.Element, 'Select element to get')
get_ele = doc.GetElement(get_ref.ElementId)

# Retrieve all parameters of the selected element
params = get_ele.GetOrderedParameters()
test_param = params[3]
print (test_param.Definition.Name)
print (test_param.AsValueString())

