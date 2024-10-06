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
class selectionfilter(ISelectionFilter):
    def AllowElement(self, element):
        if "Tags" in element.Category.Name:
            return True
        else:
            return False
        
def ToList(ele):
    if isinstance(ele,list):
        return ele
    else:
        return [ele]

def Flatten_lv3 (lst):
    return [i for sub_lst in lst for i in sub_lst]

def GetSelectedElement():
    selection = uidoc.Selection
    selectionIDs = selection.GetElementIds()
    if not selectionIDs:
        Alert('No Elements Selected. Please Select Again.',exit = True)
    elements = []
    for elementID in selectionIDs:
        elements.append(doc.GetElement(elementID))
    return elements

def GetMinPoint(ele):
    return ele.get_BoundingBox(view).Min

def GetMaxPoint(ele):
    return ele.get_BoundingBox(view).Max

def GetCenterPoint(ele):
    centroid = (GetMinPoint(ele) + GetMaxPoint(ele))/2
    return centroid

def GetCenterOfTag(tag):
    if tag.HasLeader:
        with TransactionGroup(doc,'Get Center Of Tag') as tg:
            tg.Start()

            #Deactivate Leader Line
            with Transaction(doc,'Deactivate Leader Line') as t:
                t.Start()
                tag.HasLeader = False
                t.Commit()

            #Get the center of tag
            center = GetCenterPoint(tag)

            #Activate Leader Line
            with Transaction(doc,'Activate Leader Line') as t:
                t.Start()
                tag.HasLeader = True
                t.Commit()
            
            tg.Assimilate()
    else:
        center = GetCenterPoint(tag)
    return center

# def GetCenterOfTag(tag):
#     if tag.HasLeader:
#         with TransactionGroup(doc,'Get Center Of Tag') as tg:
#             tg.Start()

#             #Deactivate Leader Line
#             with Transaction(doc,'Deactivate Leader Line') as t:
#                 t.Start()
#                 tag.HasLeader = False
#                 t.Commit()

#             #Get the center of tag
#             center = tag.TagHeadPosition

#             #Activate Leader Line
#             with Transaction(doc,'Activate Leader Line') as t:
#                 t.Start()
#                 tag.HasLeader = True
#                 t.Commit()
            
#             tg.Assimilate()
#     else:
#         center = tag.TagHeadPosition
#     return center

def PullPointOntoPlane(pt, pl):
    # Get the normal vector and origin of the plane
    normalVector = pl.Normal
    origin = pl.Origin

    # Calculate the projected points using list comprehension
    pullPoints = pt.Add(normalVector.Multiply(normalVector.DotProduct(origin) - normalVector.DotProduct(pt))) 

    return pullPoints

def CreatePlane(point,option):
    x_axis = XYZ(1,0,0)
    y_axis = XYZ(0,1,0)
    if option:
        return Plane.CreateByNormalAndOrigin(x_axis,point)
    else:
        return Plane.CreateByNormalAndOrigin(y_axis,point)

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

def SetPerpendicularTag(option):
    with TransactionGroup(doc,'Set 90 Degree Tag') as tg:
        tg.Start()

        #Select tag and extract relating points
        refs = uidoc.Selection.PickObjects(ObjectType.Element,selectionfilter(),"Select Tags")
        selectedTag = [doc.GetElement(tag.ElementId) for tag in refs]
        centerpointTag = [GetCenterOfTag(tag) for tag in selectedTag]
        taggedElement = Flatten_lv3([GetTaggedElement(tag) for tag in selectedTag])
        centerpointTaggedElement = [GetCenterPoint(ele) for ele in taggedElement]


        #Create planes base on center point of elements
        planeList = []
        for point in centerpointTaggedElement:
            plane = CreatePlane(point,option)
            planeList.append(plane)


        #Create new points for leader elbow
        leaderElbowPoint = []
        for plane,point in zip(planeList,centerpointTag):
            point = XYZ(point.X,point.Y,0)
            elbowPoint = PullPointOntoPlane(point,plane)
            leaderElbowPoint.append(elbowPoint)

        #Execute
        with Transaction(doc,'Set 90 Degree Tag') as t:
            t.Start()
            for tag,elbowPoint,endPoint in zip(selectedTag,leaderElbowPoint,centerpointTaggedElement):
                if tag.LeaderEndCondition == LeaderEndCondition.Attached:
                    try:
                        tag.LeaderEndCondition = LeaderEndCondition.Free
                        tag.LeaderElbow = elbowPoint
                        tag.LeaderEnd = endPoint
                        tag.LeaderEndCondition = LeaderEndCondition.Attached
                    except:
                        tag.LeaderEndCondition = LeaderEndCondition.Free
                        ref = tag.GetTaggedReferences()[0]
                        tag.SetLeaderElbow(ref,elbowPoint)
                        tag.SetLeaderEnd(ref,endPoint)
                        tag.LeaderEndCondition = LeaderEndCondition.Attached
                else:
                    try:
                        ref = tag.GetTaggedReferences()[0]
                        tag.SetLeaderElbow(ref,elbowPoint)
                        tag.SetLeaderEnd(ref,endPoint)
                    except:
                        pass
            t.Commit()
            
        tg.Assimilate()

def LineByStartEndPoint(point1,point2):
    return Line.CreateBound(point1,point2)

def TranslatePointByLine(point,line):
    direction = line.Direction
    length = line.Length
    vectorDist = direction.Multiply(length)
    newpoint = point.Add(vectorDist)
    return newpoint

def SetLinearTag(option):
    with TransactionGroup(doc,'Set Straight Tag') as tg:
        tg.Start()

        #Select tag and extract relating points
        refs = uidoc.Selection.PickObjects(ObjectType.Element,selectionfilter(),"Select Tags")
        selectedTag = [doc.GetElement(tag.ElementId) for tag in refs]
        centerpointTag = [GetCenterOfTag(tag) for tag in selectedTag]
        taggedElement = Flatten_lv3([GetTaggedElement(tag) for tag in selectedTag])
        centerpointTaggedElement = [GetCenterPoint(ele) for ele in taggedElement]

        #Create planes base on center point of elements
        planeList = []
        for point in centerpointTag:
            plane = CreatePlane(point,option)
            planeList.append(plane)
        
        #Create new points for tag head position
        newCenterTag = []
        for plane,point in zip(planeList,centerpointTaggedElement):
            newpoint = PullPointOntoPlane(point,plane)
            newCenterTag.append(newpoint)
    
        # Create line between old center and new center of tag
        lines = []
        for point1, point2 in zip(centerpointTag,newCenterTag):
            line = LineByStartEndPoint(point1,point2)
            lines.append(line)

        #Execute
        with Transaction(doc,'Set Linear Tag') as t:
            t.Start()
            for tag,line,center in zip(selectedTag,lines,centerpointTaggedElement):
                    if tag.LeaderEndCondition == LeaderEndCondition.Attached:
                        tagheadPoint = tag.TagHeadPosition
                        newTagHeadPoint = TranslatePointByLine(tagheadPoint,line)
                        tag.TagHeadPosition = newTagHeadPoint

                    else:
                        try:
                            tagheadPoint = tag.TagHeadPosition
                            newTagHeadPoint = TranslatePointByLine(tagheadPoint,line)
                            tag.TagHeadPosition = newTagHeadPoint
                            tag.LeaderEnd = center
                        except:
                            ref = tag.GetTaggedReferences()[0]
                            tag.SetLeaderEnd(ref,center)

            t.Commit()

        tg.Assimilate()