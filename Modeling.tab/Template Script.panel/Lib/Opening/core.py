import clr 
import math
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
version = int(app.VersionNumber)
#-------------------------------------------Function--------------------------------------------------------------------
# Select element by category
class SelectionFilter(ISelectionFilter):
    def __init__(self, categories):
        self.categories = categories

    def AllowElement(self, element):
        if element.Category.Name in self.categories:
            return True
        return False

    def AllowReference(self, reference, point):
        return False
        
def ToList(ele):
    if isinstance(ele,list):
        return ele
    else:
        return [ele]

def Flatten_lv3 (lst):
    return [i for sub_lst in lst for i in sub_lst]

def GetGeometryOfElement (ele):
    geo = []
    opt = Options() 
    opt.ComputeReferences = True 
    opt.IncludeNonVisibleObjects = False 
    opt.DetailLevel = ViewDetailLevel.Fine 
    GeoByEle = ele.get_Geometry(opt)
    geo = [i for i in GeoByEle]
    return geo

def GetSolidfromGeo(lstGeo):
    result = []
    for i in lstGeo:
        if i.GetType() == Solid and i.Volume > 0:
            result.append(i)
        elif i.GetType() == GeometryInstance:
            var = i.SymbolGeometry
            for j in var:
                if j.GetType() == Solid and j.Volume >0:
                    result.append(j)
    return result

def GetFacefromSolid(lstSolid):
    result = []
    for k in lstSolid:
        lst_faces = k.Faces
        for face in lst_faces:
            if face.Reference != None:
                result.append(face)
    return result

def GetMaxAreaFace(lstFaces):
    result = []
    maxArea = []
    for i in lstFaces:
        result.append(i.Area)
    for j in range(len(result)):
        if result[j] >= max(result)-1:
            maxArea.append(lstFaces[j])
    return maxArea

def GeometryIntersect(geo1,geo2):
    geo = BooleanOperationsUtils.ExecuteBooleanOperation(geo1, geo2, BooleanOperationsType.Intersect)
    if geo.Volume > 0 :
        return geo
    
# def UnionSolids(lstSolid):
#     union = None
#     for solid in lstSolid:
#         if union == None:
#             union = solid
#         else:
#             union = BooleanOperationsUtils.ExecuteBooleanOperation(union, solid,BooleanOperationsType.Union)
#     return union

def UnionSolids(solid_a, solids):
    if not isinstance(solids, list):
        solids = [solids]
    solids = [
        BooleanOperationsUtils.ExecuteBooleanOperation(
            solid_a, sld, BooleanOperationsType.Intersect
        )
        for sld in solids
    ]
    union = solids.pop()
    while solids:
        union = BooleanOperationsUtils.ExecuteBooleanOperation(
            union, solids.pop(), BooleanOperationsType.Union
        )
    return union

def GetCentroidSolid(solid):
    return solid.ComputeCentroid()

def GetBoundingBoxGeometry(geo):
    return geo.GetBoundingBox()

def GetMinPoint(boundingbox):
    origin = boundingbox.Transform.Origin
    return boundingbox.Min + origin

def GetMaxPoint(boundingbox):
    origin = boundingbox.Transform.Origin
    return boundingbox.Max + origin

def GetBoundingBoxElement(ele):
    return ele.get_BoundingBox(None)

def GetMinPointEle(boundingbox):
    return boundingbox.Min

def GetMaxPointEle(boundingbox):
    return boundingbox.Max

def GetCenterBoundingBox(boundingbox):
    minpoint = GetMinPoint(boundingbox)
    maxpoint = GetMaxPoint(boundingbox)
    centerpoint = (minpoint + maxpoint)/2
    return centerpoint

def solidBoundingBox(bbox):

    # Lower Corner Points from BoundingBox
    pt0 = XYZ(bbox.Min.X, bbox.Min.Y, bbox.Min.Z)
    pt1 = XYZ(bbox.Max.X, bbox.Min.Y, bbox.Min.Z)
    pt2 = XYZ(bbox.Max.X, bbox.Max.Y, bbox.Min.Z)
    pt3 = XYZ(bbox.Min.X, bbox.Max.Y, bbox.Min.Z)
    
    # Create Edges of the BoundingBox
    edge0 = Line.CreateBound(pt0, pt1)
    edge1 = Line.CreateBound(pt1, pt2)
    edge2 = Line.CreateBound(pt2, pt3)
    edge3 = Line.CreateBound(pt3, pt0)
    
    # Create CurveLoop from Edges
    edges  = [edge0, edge1, edge2, edge3]
    baseLoop = CurveLoop.Create(edges)
    loopList = [baseLoop]

  
    # Create Solid
    height = bbox.Max.Z - bbox.Min.Z
    preTransformBox = GeometryCreationUtilities.CreateExtrusionGeometry(loopList, XYZ.BasisZ, height)

    # Make sure BoundingBox has the same Transform 
    transformBox = SolidUtils.CreateTransformed(preTransformBox, bbox.Transform)

    return transformBox

def CreateBoundingBox(bbox):
    t = Transaction(doc, 'Create DirectShape from BoundingBox')
    t.Start()


    # Convert Element's BoundingBox to Solid

    solid = solidBoundingBox(bbox)

    # Create a DirectShape
    ds = DirectShape.CreateElement(doc, ElementId(BuiltInCategory.OST_GenericModel))
    ds.SetShape([solid])
        
    t.Commit()

def CreateSolid(solid):
    t = Transaction(doc, 'Create DirectShape from BoundingBox')
    t.Start()

    # Create a DirectShape
    ds = DirectShape.CreateElement(doc, ElementId(BuiltInCategory.OST_GenericModel))
    ds.SetShape([solid])
        
    t.Commit()


def GetElementType(doc,ele):
    typeId = ele.GetTypeId()
    return doc.GetElement(typeId)

def GetElementDirection(ele):
    return ele.Location.Curve.Direction

def AngleWithVector(vector1,vector2):
    return vector1.AngleTo(vector2)

def AngleAboutAxis(vector1,vector2,axis):
    angle = vector1.AngleOnPlaneTo(vector2,axis)
    return angle

def RotateGeometry(geometry, origin, axis, angle):
    rotationTransform = Transform.CreateRotationAtPoint(axis, angle, origin)
    result = []
    transformedGeoObject = SolidUtils.CreateTransformed(geometry,rotationTransform)
    result.append(transformedGeoObject)
    return result

def GetEditableFamily(doc):
    #Retrieve all families that are not system families in current doc
    allFamilies = FilteredElementCollector(doc).OfClass(Family).ToElements()

    #Filter the editable families and resultput result
    editableFamilies = []
    for i in allFamilies:
        if (i.IsEditable):
            editableFamilies.append(i)
    
    return editableFamilies

def GetFamilySymbolFromFamily(family):
    IdHashSet = family.GetFamilySymbolIds()
    IdLst = list(IdHashSet)
    return doc.GetElement(IdLst[0])

def PlaceFamilyInstanceByFaceAndPoint(face,familyType,point):
    ref = face.Reference
    faceNormal = face.FaceNormal
    direction = faceNormal.CrossProduct(XYZ.BasisZ)

    with Transaction(doc,"Place Family Instance") as t:
        t.Start()
        result = doc.Create.NewFamilyInstance(ref, point, direction, familyType)
        t.Commit()

    return result

def SetParameterByName(ele,parameterName,value):
    with Transaction(doc,"Set parameter element") as t:
        t.Start()
        ele.LookupParameter(parameterName).Set(value)
        t.Commit()
    
    return ele

def convertToFeet(value):
    # displayUnit = doc.GetUnits().GetFormatOptions(UnitType.UT_HVAC_Airflow).DisplayUnits
    displayUnit = UnitTypeId.Millimeters
    result = UnitUtils.ConvertToInternalUnits(value, displayUnit)
    return result

def convertToMilimeter(value):
    # displayUnit = doc.GetUnits().GetFormatOptions(UnitType.UT_HVAC_Airflow).DisplayUnits
    displayUnit = UnitTypeId.Millimeters
    result = UnitUtils.ConvertFromInternalUnits(value, displayUnit)
    return result