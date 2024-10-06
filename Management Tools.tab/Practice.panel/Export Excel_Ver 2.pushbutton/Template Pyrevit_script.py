#!/usr/bin/env python
# -*- coding: utf-8 -*-
import clr 
import math
import xlsxwriter
import os
from collections import OrderedDict
from pyrevit import revit,forms,script
from pyrevit.forms import ProgressBar
from Autodesk.Revit.UI.Selection import ObjectType 
from System.Collections.Generic import *
from rpw.ui.forms import Alert
import csv

#WPF
try:
    clr.AddReference('IronPython.wpf')
    clr.AddReference('PresentationCore')
    clr.AddReference('PresentationFramework')
except IOError:
    raise
from System.IO import StringReader
from System.Windows.Markup import XamlReader, XamlWriter
from System.Windows import Window,Application
from System.Windows import RoutedEventHandler
try:
    import wpf
except ImportError:
    raise


clr.AddReference('ProtoGeometry')
import Autodesk.DesignScript.Geometry as DSGeo
from Autodesk.DesignScript.Geometry import *

clr.AddReference('RevitAPI')
import Autodesk
from Autodesk.Revit.DB import *

clr.AddReference('RevitAPIUI')
from  Autodesk.Revit.UI import*

clr.AddReference('RevitAPIUI')
from  Autodesk.Revit.UI.Selection import*

clr.AddReference('RevitServices')
import RevitServices
from RevitServices.Persistence import DocumentManager
from RevitServices.Transactions import TransactionManager


doc = __revit__.ActiveUIDocument.Document
view = doc.ActiveView
uidoc = __revit__.ActiveUIDocument
app = __revit__.Application
DB = Autodesk.Revit.DB
output = script.get_output()
#----------------------------------Main Logic---------------------------------------------------------------------------
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

class Viewmodel():
    def __init__(self, gvcId, gvcfamType, gvcthickness, gvcvolume):
        self._gvcId = gvcId
        self._gvcfamType = gvcfamType
        self._gvcthickness = gvcthickness
        self._gvcvolume = gvcvolume

    @property
    def gvcId(self):
        return self._gvcId
    
    @property
    def gvcfamType(self):
        return self._gvcfamType
    
    @property
    def gvcthickness(self):
        return self._gvcthickness
    
    @property
    def gvcvolume(self):
        return self._gvcvolume
    

class MyWindow(Window):
    def __init__(self):
        self.ui = wpf.LoadComponent(self,r'D:\\Home\\Python Revit API\BIM 3DM\Studying\\Create Forms (WPF)\\WPF_Lesson1.xaml')
        self.selected_elements = []
        self.lvElements.ItemsSource = self.selected_elements
        self.ui.btnClear.Click += RoutedEventHandler(self.btn_Clear_Click)
    
    def btn_Clear_Click(self,sender,event):
        self.selected_elements.Clear()
        self.lvElements.Items.Refresh()
        # pass


    def btn_PickObjects_Click(self,sender,event):
        select_ele = selectionfilter('NOT','Floors')
        self.Hide()
        familyinstances = uidoc.Selection.PickElementsByRectangle(select_ele,'Select')


        global eles,ids,names,thickness_values,volume_values

        eles = [doc.GetElement(i.Id) for i in familyinstances]
        ids = [i.Id.IntegerValue for i in eles]
        names = [i.Name for i in eles]
        thickness_values = [round(i.LookupParameter('Thickness').AsDouble()*304.8) for i in eles]
        volume_values = [round(i.LookupParameter('Volume').AsDouble()*0.0283,3) for i in eles]
        viewModels = []
        for id,name,thickness,volume in zip(ids,names,thickness_values,volume_values):
            viewModel = Viewmodel(
                gvcId= id,
                gvcfamType= name,
                gvcthickness= thickness,
                gvcvolume= volume,
            )
            
            viewModels.append(viewModel)

        for eleInViewModel in viewModels:
            self.selected_elements.Add(eleInViewModel)

        self.Show()
        pass


    def btn_Export_Click(self,sender,event):
        pass

    def btn_Cancel_Click(self,sender,event):
        self.Close()


mywindow = MyWindow()
mywindow.ShowDialog()
# eles = mywindow.btn_PickObjects_Click(self,sender,event)
# print (eles)
# print (ids)
# print (names)
# print (thickness)
# print (volume)

