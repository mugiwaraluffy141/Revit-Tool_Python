#!/usr/bin/env python
# -*- coding: utf-8 -*-
'''
Function: Track Filter In Active View Can Control Your Element.
-----------------------------------------------------------------
User Manual: Select an element to track
-----------------------------------------------------------------
'''
import clr 
from pyrevit import revit,forms,script
from Autodesk.Revit.UI.Selection import ObjectType 
from System.Collections.Generic import *

clr.AddReference('RevitAPI')
import Autodesk
from Autodesk.Revit.DB import *

clr.AddReference('RevitAPIUI')
from  Autodesk.Revit.UI import*

clr.AddReference('RevitAPIUI')
from  Autodesk.Revit.UI.Selection import*


doc = __revit__.ActiveUIDocument.Document
view = doc.ActiveView
uidoc = __revit__.ActiveUIDocument
app = __revit__.Application
DB = Autodesk.Revit.DB
output = script.get_output()
version = app.VersionNumber

from Filter.core import *

#----------------------------------Main Logic-------------------------------------------------------------------------
# Get information of filters
filterIdList = GetFilterIdInView(view)
filterName = [doc.GetElement(Id).Name for Id in filterIdList]
filterDict = dict(zip(filterName,filterIdList))
filterParamId = [GetParameterIdFromFilter(Id) for Id in filterIdList]

noruleFilter = CountParamFilter(filterParamId,filterIdList)[0]
oneruleFilter = CountParamFilter(filterParamId,filterIdList)[1]
moreruleFilter = CountParamFilter(filterParamId,filterIdList)[2]

affectFilter = []
if len(filterName) == 0:
    TaskDialog.Show("Result","There is no filter in your view.")
else:
    #Get information from element
    ref = uidoc.Selection.PickObject(ObjectType.Element,'Select Element')
    element = doc.GetElement(ref)
    eleCategoryId = GetElementCategoryId(element)
    eleParamId = GetElementParameterId(element)
    eleParamName = GetElementParameterName(element)
    paramDict = dict(zip(eleParamId,eleParamName))

    # No rule filter
    noruleCategoryId = [GetCategoryFromFilter(Id) for Id in noruleFilter]
    noruleFilterName = [doc.GetElement(Id).Name for Id in noruleFilter]
    for ind,sublst in enumerate(noruleCategoryId):
        if eleCategoryId in sublst:
            affectFilter.append(noruleFilterName[ind])

    #One rule filter
    # Check category
    oneruleCategoryId = [GetCategoryFromFilter(Id) for Id in oneruleFilter]
    oneruleFilterName = [doc.GetElement(Id).Name for Id in oneruleFilter]
    oneruleFilterParamId = [GetParameterIdFromFilter(Id) for Id in oneruleFilter]

    checkCategory = []
    for sublst in oneruleCategoryId:
        temp = False
        if eleCategoryId in sublst:
            temp = True
        checkCategory.append(temp)

    # Check parameter
    checkParam = []
    validParamName = []
    for sublst in oneruleFilterParamId:  
        temp = True
        for filterParam in sublst:  
            if filterParam not in eleParamId:
                temp = False
                break
            else:
                validParamName.append(paramDict.get(filterParam))
        checkParam.append(temp)

    #Check value of parameter
    checkValueParam = []
    for i in range(len(oneruleFilterName)):
        if checkCategory[i] and checkParam[i]:
            filterId = oneruleFilter[i]
            filterEvaluator = GetFilterEvaluator(filterId)
            filterParamValue = GetParameterValueFilter(filterId)

            # Get parameter value from element
            eleParamValue = []
            for paramName in validParamName:
                value = GetParamValue(element, paramName)
                eleParamValue.append(value)

            # Compare
            flag = False
            for sublst in eleParamValue:
                for eleValue in sublst:
                    for evaluator, filterValue in zip(filterEvaluator, filterParamValue):
                        if CheckValue(eleValue, filterValue, evaluator):
                            checkValueParam.append(True)
                            affectFilter.append(oneruleFilterName[i])
                            flag = True
                            break
                    if flag:
                        break
                if flag:
                    break

    # Print the result
    # Filter has no rule or one rule
    if len(affectFilter) == 0:
        print ("There is no filter can affect your element.")
    else:
        print ("Filters may affect your element:")
        for filter in affectFilter:
            print ("_ " + filter)
    print ("-----------------------------------------------------------------------")

    # Filter has more than one rule
    moreruleFilterName = [doc.GetElement(Id).Name for Id in moreruleFilter]
    if len(moreruleFilterName) != 0:
        print ("This tool cannot track these filters. They may affect your element:")
        for filter in moreruleFilterName:
            print ("_ " + filter)