import clr 
from pyrevit import revit,forms,script
from Autodesk.Revit.UI.Selection import ObjectType 
from System.Collections.Generic import *
from rpw.ui.forms import Alert

clr.AddReference('RevitAPI')
import Autodesk
from Autodesk.Revit.DB import *

clr.AddReference('RevitAPIUI')
from  Autodesk.Revit.UI import*
from  Autodesk.Revit.UI.Selection import*

doc = __revit__.ActiveUIDocument.Document
view = doc.ActiveView
uidoc = __revit__.ActiveUIDocument
app = __revit__.Application
DB = Autodesk.Revit.DB
output = script.get_output()
version = int(app.VersionNumber)
#-------------------------------------------Function--------------------------------------------------------------------
def GetFilterIdInView(view):
    filterId = view.GetFilters()
    return filterId

def GetCategoryFromFilter(filterId):
    categoryListId = doc.GetElement(filterId).GetCategories()
    categoryId = []
    for Id in categoryListId:
        categoryId.append(Id.IntegerValue)
    return categoryId

def GetParameterIdFromFilter(filterId):
    paramFilterElement = doc.GetElement(filterId)
    try:
        parameterId = [Id.IntegerValue for Id in paramFilterElement.GetElementFilterParameters()]
    except:
        parameterId = None
    return parameterId

def GetFilterEvaluator(filterId):
    result = []
    paramFilterElement = doc.GetElement(filterId)
    try:
        elementFilter = paramFilterElement.GetElementFilter().GetFilters()
        for filter in elementFilter:
            filterRule = filter.GetRules()
            for rule in filterRule:
                try:
                    evaluator = rule.GetEvaluator().ToString().Replace('Autodesk.Revit.DB.','')
                    result.append(evaluator)
                except:
                    try:
                        evaluator = rule.GetInnerRule().GetEvaluator().ToString().Replace('Autodesk.Revit.DB.','') + '_Not'
                        result.append(evaluator)
                    except:
                        result.append(rule.ToString().Replace('Autodesk.Revit.DB.',''))
    except:
        result.append(None)
    return result

def GetParameterValueFilter(filterId):
    result = []
    paramFilterElement = doc.GetElement(filterId)
    try:
        elementFilter = paramFilterElement.GetElementFilter().GetFilters()
        for filter in elementFilter:
            filterRule = filter.GetRules()
            for rule in filterRule:
                try:
                    #Get value of normal evaluator
                    try:
                        value = rule.RuleValue
                        result.append(value)
                    except:
                        value = rule.RuleString
                        result.append(value)
                except:
                    try:
                        #Get value of "not" evaluator
                        try:
                            value = rule.GetInnerRule().RuleValue
                            result.append(value)
                        except:
                            value = rule.GetInnerRule().RuleString
                            result.append(value)
                    except:
                        #Get value of has value/ has no value
                        result.append('Has / Has No Value')
    except:
        result.append(None)
    return result

def GetElementCategoryId(element):
    return element.Category.Id.IntegerValue

def GetElementParameterId(element):
    result = []
    #Get instance parameters
    instanceParams = element.Parameters
    for param in instanceParams:
        paramName = param.Definition.Id.IntegerValue
        result.append(paramName)
    
    #Get type parameters
    typeId = element.GetTypeId()
    typeParams = doc.GetElement(typeId).Parameters
    for param in typeParams:
        paramName = param.Definition.Id.IntegerValue
        result.append(paramName)

    return result

def GetElementParameterName(element):
    result = []
    #Get instance parameters
    instanceParams = element.Parameters
    for param in instanceParams:
        paramName = param.Definition.Name
        result.append(paramName)
    
    #Get type parameters
    typeId = element.GetTypeId()
    typeParams = doc.GetElement(typeId).Parameters
    for param in typeParams:
        paramName = param.Definition.Name
        result.append(paramName)

    return result

def GetParamValue(ele,paramName):
    try:
        p = ele.LookupParameter(paramName)
        if p.StorageType == StorageType.Double:
            return [p.AsDouble()]
        elif p.StorageType == StorageType.Integer:
            return [p.AsInteger()]
        elif p.StorageType == StorageType.ElementId:
            return [p.AsElementId(), p.AsValueString()]
        else:
            return [p.AsValueString()]
    except:
        return "Parameter doesn't exist or its value is not available"

def CheckValue(value1,value2,evaluator):
    #value1: value from element
    #value2: value from filter
    try:
        if evaluator.endswith("Contains"):
            return value2 in value1
        elif evaluator.endswith("Contains_Not"):
            return value2 not in value1
        elif evaluator.endswith("Equals"):
            return value1 == value2
        elif evaluator.endswith("Equals_Not"):
            return value1 != value2
        elif evaluator.endswith("Greater"):
            return value1 > value2
        elif evaluator.endswith("GreaterOrEqual"):
            return value1 >= value2 
        elif evaluator.endswith("Less"):
            return value1 < value2 
        elif evaluator.endswith("LessOrEqual"):
            return value1 <= value2
        elif evaluator.endswith("BeginsWith"):
            return value1.startswith(value2)
        elif evaluator.endswith("BeginsWith_Not"):
            return not value1.startswith(value2)
        elif evaluator.endwith("EndsWith"):
            return value1.endswith(value2)
        elif evaluator.endwith("EndsWith_Not"):
            return not value1.endswith(value2)
        elif evaluator.startswith("HasValue"):
            return value1 != None
        elif evaluator.startswith("HasNoValue"):
            return value1 == None
        else:
            return "Invalid Evaluator"
    except:
        pass
    
def Flatten_lv3 (lst):
    return [i for sub_lst in lst for i in sub_lst]

def CountParamFilter(filterParamId,filterIdList):
    noRuleFilter, oneRuleFilter, moreRuleFilter = [],[],[]
    for ind,sublst in enumerate(filterParamId):
        if len(sublst) == 0:
            noRuleFilter.append(filterIdList[ind])
        elif len(sublst) == 1:
            oneRuleFilter.append(filterIdList[ind])
        else:
            moreRuleFilter.append(filterIdList[ind])
    return noRuleFilter, oneRuleFilter, moreRuleFilter