#!/usr/bin/env python
# -*- coding: utf-8 -*-
import clr 
import math
from pyrevit import forms
from rpw.ui.forms import Alert

clr.AddReference('ProtoGeometry')
import Autodesk.DesignScript.Geometry as DSGeo
from Autodesk.DesignScript.Geometry import *

clr.AddReference('RevitAPI')
import Autodesk
from Autodesk.Revit.DB import *

doc = __revit__.ActiveUIDocument.Document
view = doc.ActiveView
uidoc = __revit__.ActiveUIDocument
app = __revit__.Application
DB = Autodesk.Revit.DB
version = app.VersionNumber

#----------------------------------Function-----------------------------------------------------------------------------
def CreateDatumLine(boundLines, grid):
    gridLine = None
    curveG = grid.Curve
    vectGrid = curveG.Direction
    lstPtToLine = []
    for lineBound in boundLines:
        rayc = DB.Line.CreateUnbound(XYZ(curveG.Origin.X, curveG.Origin.Y, lineBound.GetEndPoint(0).Z), vectGrid)
        outInterR = clr.Reference[IntersectionResultArray]()
        result = rayc.Intersect(lineBound, outInterR)
        if result == SetComparisonResult.Overlap:
            interResult = outInterR.Value
            lstPtToLine.append(interResult[0].XYZPoint)
    if len(lstPtToLine) == 2:
        P1 = lstPtToLine[0]
        P2 = lstPtToLine[1]
        TransXYZ1 = DSGeo.Point.ByCoordinates(P1.X, P1.Y, P1.Z)
        TransXYZ2 = DSGeo.Point.ByCoordinates(P2.X, P2.Y, P2.Z)
        TransPoint1 = XYZ(TransXYZ1.X, TransXYZ1.Y, TransXYZ1.Z)
        TransPoint2 = XYZ(TransXYZ2.X, TransXYZ2.Y, TransXYZ2.Z)
        gridLine = Autodesk.Revit.DB.Line.CreateBound(TransPoint1, TransPoint2)
    return gridLine

#----------------------------------Main Logic---------------------------------------------------------------------------
allViews = FilteredElementCollector(doc).OfCategory(BuiltInCategory.OST_Views).WhereElementIsNotElementType().ToElements()
planViews = [view for view in allViews if view.ViewDirection.Z == 1]
planViewNames = [view.Name for view in planViews]
viewDict = dict(zip(planViewNames, planViews))

planViewsOption = {'Plan Views': sorted(viewDict)}

selectedViewNames = forms.SelectFromList.show(planViewsOption,
                                              multiselect=True,
                                              group_selector_title='Select View',
                                              button_name='OK')
if not selectedViewNames:
    Alert('No Source View Selected. Please Select Again.', exit=True)

lstInputViews = [viewDict.get(name) for name in selectedViewNames]

with Transaction(doc, 'Grid to Crop Box') as t:
    t.Start()
    rotaionAngleListLIST = []

    for activView in lstInputViews:
        activView.CropBoxVisible = True
        doc.Regenerate()

        cropBox = activView.CropBox

        fecGrids = FilteredElementCollector(doc, activView.Id).OfClass(DatumPlane).ToElements()
        cutOffset = fecGrids[0].GetCurvesInView(DatumExtentType.ViewSpecific, activView)[0].GetEndPoint(0).Z
        fecGrids = [x for x in fecGrids if isinstance(x, DB.Grid)]

        outLst = []
        newGLineList = []
        shpManager = activView.GetCropRegionShapeManager()
        boundLines = shpManager.GetCropShape()[0]
        startpointList = []
        endpointList = []
        rotationAngleList = []

        if activView.ViewDirection.IsAlmostEqualTo(XYZ(0, 0, 1)):
            currentZ = list(boundLines)[0].GetEndPoint(0).Z
            tf = Transform.CreateTranslation(XYZ(0, 0, cutOffset - currentZ))
            boundLines = CurveLoop.CreateViaTransform(boundLines, tf)
            for grid in fecGrids:
                outLst.append(grid.Curve)
                newGLine = CreateDatumLine(boundLines, grid)
                newGLineList.append(newGLine)
                if newGLine is not None:
                    grid.SetCurveInView(DatumExtentType.ViewSpecific, activView, newGLine)
        else:
            for grid in fecGrids:
                outLst.append(grid.Curve)
                newGLine = CreateDatumLine(boundLines, grid)
                newGLineList.append(newGLine)
                if newGLine is not None:
                    grid.SetCurveInView(DatumExtentType.ViewSpecific, activView, newGLine)

        for newGLine in newGLineList:
            startpointXYZ = newGLine.GetEndPoint(0)
            endpointXYZ = newGLine.GetEndPoint(1)
            startpoint = DSGeo.Point.ByCoordinates(startpointXYZ.X, startpointXYZ.Y, startpointXYZ.Z)
            endpoint = DSGeo.Point.ByCoordinates(endpointXYZ.X, endpointXYZ.Y, endpointXYZ.Z)
            startpointList.append(startpoint)
            endpointList.append(endpoint)

            vector = newGLine.Direction
            rotationAngle = abs(math.degrees(vector.AngleOnPlaneTo(activView.RightDirection, XYZ.BasisZ)))
            rotationAngleList.append(rotationAngle)
        rotaionAngleListLIST.append(rotationAngleList)

    t.Commit()