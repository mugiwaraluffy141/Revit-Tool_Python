'''
Function: Connect Sprinkler Head To Pipe.
-----------------------------------------------------------------
User Manual:
_ Step 1: Select Main Pipe
_ Step 2: Select Sprinkler Heads
-----------------------------------------------------------------
***Attention:
If the tool does not work, try to select a smaller area of Sprinkler
'''
import clr 
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
#-------------------------------------------------------------------------------
class selectionfilter(ISelectionFilter):
    def __init__(self,category):
        self.category = category

    def AllowElement(self, element):
        if element.Category.Name == self.category:
            return True
        else:
            return False
        
def tolist(ele):
    if isinstance(ele,list):
        return ele
    else:
        return [ele]

def flatten_lv3 (lst):
    return [i for sub_lst in lst for i in sub_lst]

def get_ele_connectors(elements):
    result = []
    for element in elements:
        try:
            connectors = element.MEPModel.ConnectorManager.Connectors
        except:
            try:
                connectors = element.ConnectorManager.Connectors
            except:
                connectors = []
        result.append([i for i in connectors])
    return result

def pull_point_onto_plane(pts, pl):
    # Get the normal vector and origin of the plane
    n = pl.Normal
    o = pl.Origin

    # Calculate the projected points using list comprehension
    pull_pts = [pt.Add(n.Multiply(n.DotProduct(o) - n.DotProduct(pt))) for pt in pts]

    return pull_pts

def pipe_by_connector_endpoint(pipetype,level,connectors,endpoints):
    ele = []
    with Transaction(doc,'Create pipe by connector and end point') as t:
        t.Start()
        for connector,endpoint in zip(connectors,endpoints):
            try:
                pipe = DB.Plumbing.Pipe.Create(doc,pipetype,level,connector,endpoint)
                ele.append(pipe)
            except:
                pass
        t.Commit()
    return ele

def pipe_by_start_end_point(systemtype,pipetype,level,start,end):
    ele = []
    with Transaction(doc,'Create pipe by start and end point') as t:
        t.Start()
        for i,j in zip(start,end):
            try:
                pipe = DB.Plumbing.Pipe.Create(doc,systemtype,pipetype,level,i,j)
                ele.append(pipe)
            except:
                pass
        t.Commit()
    return ele

def closest_connectors_elbow(pipe1, pipe2):
	conn1 = pipe1.ConnectorManager.Connectors
	conn2 = pipe2.ConnectorManager.Connectors
	
	dist = 100000000
	connset = None
	for c in conn1:
		for d in conn2:
			conndist = c.Origin.DistanceTo(d.Origin)
			if conndist < dist:
				dist = conndist
				connset = [c,d]
	return connset

def elbow_by_connector(lst_pipe1,lst_pipe2):
    ele = []
    for pipe1,pipe2 in zip(lst_pipe1,lst_pipe2):
        connectors = closest_connectors_elbow(pipe1,pipe2)
        with Transaction(doc,'Create elbow') as t:
            t.Start()
            try:
                elbow = doc.Create.NewElbowFitting(connectors[0],connectors[1])
                ele.append(elbow)
            except:
                pass
            t.Commit()
    return ele

def split_pipe_at_point(pipe,pts):
    ele = []
    with Transaction(doc,'Split Pipe by Point') as t:
        t.Start()

        for pt in pts:
            ele.append(DB.Plumbing.PlumbingUtils.BreakCurve(doc, pipe.Id, pt))
        ele.append(pipe.Id)
        result = [[doc.GetElement(ele[i]), doc.GetElement(ele[i+1])] for i in range(len(ele) - 1)]

        t.Commit()
    return result

def closest_connectors_tee(pipe1, pipe2,pipe3):
	conn1 = pipe1.ConnectorManager.Connectors
	conn2 = pipe2.ConnectorManager.Connectors
	conn3 = pipe3.ConnectorManager.Connectors
	
	dist1 = 100000000
	dist2 = 100000000
	connset = []
	for c in conn1:
		for d in conn2:
			conndist = c.Origin.DistanceTo(d.Origin)
			if conndist < dist1:
				dist1 = conndist
				c1 = c
				d1 = d
		for e in conn3:
			conndist = c.Origin.DistanceTo(e.Origin)
			if conndist < dist2:
				dist2 = conndist
				e1 = e
		connset = [c1,d1,e1]
	return connset

def tee_by_main_and_branch(lst_pipe):
    for sub_lst in lst_pipe:
        connectors = closest_connectors_tee(sub_lst[0],sub_lst[1],sub_lst[2])
        result = []
        with Transaction(doc,'Create Tee') as t:
            t.Start()
            try:
                result.append(doc.Create.NewTeeFitting(connectors[0],connectors[1],connectors[2]))
            except:
                pass
            t.Commit()
    return result

def closest_connectors_tap(pipe1, pipe2):
	conn1 = pipe1.ConnectorManager.Connectors
	line = pipe2.Location.Curve
	
	dist = 100000000
	conn = None
	for c in conn1:
		conndist = line.Project(c.Origin).Distance
		if conndist < dist:
			dist = conndist
			conn = c
	return conn

def tap_by_main_and_branch(lst_branch,main_pipe):
    result = []
    for pipe in lst_branch:
        connectors = closest_connectors_tap(pipe,main_pipe)
        with Transaction(doc,'Create Tap') as t:
            t.Start()
            try:
                result.append(doc.Create.NewTakeoffFitting(connectors,main_pipe))
            except:
                pass
            t.Commit()
    return result

#Pipe
pipe_filter = selectionfilter('Pipes')
selected_piperef = uidoc.Selection.PickObject(ObjectType.Element,pipe_filter,'Select Main Pipe')
selected_pipe = doc.GetElement(selected_piperef.ElementId)
pipe_origin = selected_pipe.Location.Curve.Origin
z_axis = XYZ(0,0,1)
plane_pipe_xy = Plane.CreateByNormalAndOrigin(z_axis,pipe_origin)
pipe_direction = selected_pipe.Location.Curve.Direction
plane_pipe_z = Plane.CreateByNormalAndOrigin(z_axis.CrossProduct(pipe_direction),pipe_origin)

#Sprinkler
spr_filter = selectionfilter('Sprinklers')
selected_spr = uidoc.Selection.PickElementsByRectangle(spr_filter,'Select Sprinkler Heads')
spr_connectors = flatten_lv3(get_ele_connectors(selected_spr)) 
spr_connector_origin = [connector.Origin for connector in spr_connectors]

#-------------------------------Draw pipe---------------------------------------
#Create new point by project the origin point onto the plane
lst_pt1 = pull_point_onto_plane(spr_connector_origin,plane_pipe_xy)
lst_pt2 = pull_point_onto_plane(lst_pt1,plane_pipe_z)

with TransactionGroup(doc,'Create Pipe from SPR head') as tg:
    tg.Start()

    pipe_typeId = selected_pipe.PipeType.Id
    pipe_levelId = selected_pipe.ReferenceLevel.Id
    pipe_systemId = selected_pipe.MEPSystem.GetTypeId()
    pipe1 = pipe_by_connector_endpoint(pipe_typeId,pipe_levelId,spr_connectors,lst_pt1)
    pipe2 = pipe_by_start_end_point(pipe_systemId,pipe_typeId,pipe_levelId,lst_pt1,lst_pt2)

    #Set pipe2 size
    with Transaction(doc,'Set DN for pipe 2 from pipe 1') as t:
        t.Start()
        result = []
        for i,j in zip(pipe1,pipe2):
            try:
                diameter = i.LookupParameter('Diameter').AsValueString()
                j.LookupParameter('Diameter').SetValueString(diameter)
                result.append(j)
            except Exception as er:
                result.append(er)
        t.Commit()

    #Create elbow between 2 pipes
    new_elbow = elbow_by_connector(pipe1,pipe2)

    #Create Junction
    junctiontype = doc.GetElement(pipe_typeId).RoutingPreferenceManager.PreferredJunctionType

    if str(junctiontype) == 'Tap':
        #Create Tap
        new_tap = tap_by_main_and_branch(pipe2,selected_pipe)
    else:
        #Create Tee
        split_pipe = split_pipe_at_point(selected_pipe,lst_pt2)
        lst_pipe = [[sub_lst[0], sub_lst[1], value] for sub_lst, value in zip(split_pipe, pipe2)]
        new_tee = tee_by_main_and_branch(lst_pipe)
    tg.Assimilate()

