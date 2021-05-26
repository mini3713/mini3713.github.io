"""
sample.geojson
{
"type": "FeatureCollection",
"crs": { "type": "name", "properties": { "name": "urn:ogc:def:crs:EPSG::5179" } },
"features": [
{ "type": "Feature", "properties": { "ELEVATION": 86.366000, "BLDG_H_GRD": 9.000000 }, "geometry": { "type": "MultiPolygon", "coordinates": [ [ [ [ 954500.23712887894, 1949631.5497937908 ], [ 954494.88178503397, 1949626.4041389083 ], [ 954486.86899364996, 1949635.6561309656 ], [ 954492.39222866215, 1949639.8904212238 ], [ 954500.23712887894, 1949631.5497937908 ] ] ] ] } },
{ "type": "Feature", "properties": { "ELEVATION": 89.055000, "BLDG_H_GRD": 10.200000 }, "geometry": { "type": "MultiPolygon", "coordinates": [ [ [ [ 954505.21004369832, 1949626.4383810216 ], [ 954497.39477998379, 1949619.2425518287 ], [ 954493.1117052373, 1949624.0135174387 ], [ 954501.08706631768, 1949631.2384844164 ], [ 954505.21004369832, 1949626.4383810216 ] ] ] ] } },
{ "type": "Feature", "properties": { "ELEVATION": 91.442000, "BLDG_H_GRD": 0.000000 }, "geometry": { "type": "MultiPolygon", "coordinates": [ [ [ [ 954507.8029442078, 1949623.4938485734 ], [ 954502.83574490668, 1949619.1347452225 ], [ 954502.27216590289, 1949619.3636608864 ], [ 954500.28702308412, 1949618.2436254704 ], [ 954499.38958800654, 1949619.6048090158 ], [ 954505.78312445979, 1949625.6277245362 ], [ 954507.8029442078, 1949623.4938485734 ] ] ] ] } }
]
}
"""
# Import standard library modules
import json
# Import Rhino modules
import Rhino
from Rhino.Geometry import *
from scriptcontext import doc
# import .NET libraries
import System
import math
def addRhinoLayer(layerName, layerColor=System.Drawing.Color.Black):
"""Creates a Layer in Rhino using a name and optional color. Returns the
index of the layer requested. If the layer
already exists, the color is updated and no new layer is created."""
docLyrs = doc.Layers
layerIndex = docLyrs.Find(layerName, True)
if layerIndex == -1:
layerIndex = docLyrs.Add(layerName,layerColor)
else: # it exists
layer = docLyrs[layerIndex] # so get it
if layer.Color != layerColor: # if it has a different color
layer.Color = layerColor # reset the color
return layerIndex
def PointToRhinoPoint(coordinates, elevation):
if len(coordinates) > 2:
z = coordinates[2]
else:
z = elevation
x, y = coordinates[0], coordinates[1]
return Point3d(x, y, z)
def MultiPointToRhinoPoint(coordinates, elevation):
rhPointList = []
for point in coordinates:
rhPointList.append(PointToRhinoPoint(point, elevation))
return rhPointList
def MeshToRhinoMesh(coordinates, faces):
rhMesh = Mesh()
for point in coordinates:
rhPoint = PointToRhinoPoint(point)
rhMesh.Vertices.Add(rhPoint)
for face in faces:
i, j, k = tuple(face)
mFace = MeshFace(i, j, k)
rhMesh.Faces.AddFace(mFace)
rhMesh.Normals.ComputeNormals()
rhMesh.Compact()
return rhMesh
def LineStringToRhinoCurve(coordinates, elevation):
rhPoints = MultiPointToRhinoPoint(coordinates, elevation)
return Curve.CreateControlPointCurve(rhPoints, 1)
def MultiLineStringToRhinoCurve(coordinates):
rhCurveList = []
for lineString in coordinates:
rhCurveList.append(LineStringToRhinoCurve(lineString))
return rhCurveList
def PolygonToRhinoCurve(coordinates, height, elevation):
# each ring is a separate list of coordinates
ringList = []
for ring in coordinates:
rc = LineStringToRhinoCurve(ring, elevation)
pgm = Rhino.Geometry.Extrusion.Create(rc, height*-1, True)
ringList.append(pgm)
return ringList
def MultiPolygonToRhinoCurve(coordinates, height, elevation):
polygonList = []
for polygon in coordinates:
pg = PolygonToRhinoCurve(polygon, height, elevation)
polygonList.append(pg)
return polygonList
def GeometryCollectionToParser(geometries):
pass # I need to figure this one out still
def addPoint(rhPoint, objAtt):
return doc.Objects.AddPoint(rhPoint, objAtt)
def addPoints(rhPoints, objAtt):
guidList = []
for rhPoint in rhPoints:
guidList.append(doc.Objects.AddPoint(rhPoint, objAtt))
return guidList
def addCurve(rhCurve, objAtt):
return doc.Objects.AddExtrusion(rhCurve, objAtt)
def addCurves(rhCurves, objAtt):
guidList = []
for curve in rhCurves:
guidList.append(addCurve(curve, objAtt))
return guidList
def addPolygon(ringList, objAtt):
# for now this just makes curves
# but maybe it should make TrimmedSrfs
# or should group the rings
return addCurves(ringList, objAtt)
def addPolygons(polygonList, objAtt):
guidList = []
for polygon in polygonList:
# !! Extending the guid list !!!
guidList.extend(addPolygon(polygon, objAtt))
return guidList
def addMesh(rhMesh, objAtt):
return doc.Objects.AddMesh(rhMesh, objAtt)
geoJsonGeometryMap = {
'Point':(PointToRhinoPoint, addPoint),
'MultiPoint':(MultiPointToRhinoPoint, addPoints),
'LineString':(LineStringToRhinoCurve, addCurve),
'MultiLineString':(MultiLineStringToRhinoCurve, addCurves),
'Polygon':(PolygonToRhinoCurve, addPolygon),
'MultiPolygon':(MultiPolygonToRhinoCurve, addPolygons),
'Mesh':(MeshToRhinoMesh, addMesh),
'GeometryCollection':(GeometryCollectionToParser),
}
def setUserKeys(properties, objAttributes):
for key in properties:
objAttributes.SetUserString(key, str(properties[key]))
return objAttributes
def jsonToRhinoCommon(jsonFeature):
# deal with the geometry
geom = jsonFeature['geometry']
geomType = geom['type'] # this will return a mappable string
coordinates = geom['coordinates']
elevation = jsonFeature['properties']['ELEVATION'] #이 부분은 건물의 바닥면 해발고도 속성 이름(m)
height = jsonFeature['properties']['BLDG_H_GRD'] #이 부분은 건물의 높이 속성 이름(m)
# if this is a mesh, pass the faces
if geomType == 'Mesh':
faces = geom['faces']
rhFeature = geoJsonGeometryMap[geomType][0](coordinates, faces)
# translate the coordinates to Rhino.Geometry objects
else:
rhFeature = geoJsonGeometryMap[geomType][0](coordinates, height, elevation) #만약, 고저차 없이 평지에 건물을 두려면 여기서 elevation대신 0으로 대체한다.
return rhFeature
def addJsonFeature(jsonFeature, objAttributes):
# deal with the properties
if jsonFeature['properties']:
objAttributes = setUserKeys(jsonFeature['properties'], objAttributes)
geomType = jsonFeature['geometry']['type']
rhFeature = jsonToRhinoCommon(jsonFeature)
# return the GUID(s) for the feature
return geoJsonGeometryMap[geomType][1](rhFeature, objAttributes)
def processGeoJson(parsedGeoJson,
destinationLayer=None,
destinationLayerColor=System.Drawing.Color.Black):
# get the features
jsonFeatures = parsedGeoJson['features']
guidResults = []
# set up object attributes
for jsonFeature in jsonFeatures: # for each feature
att = Rhino.DocObjects.ObjectAttributes()
# setup layer if requested
if destinationLayer != None:
att.LayerIndex = addRhinoLayer(destinationLayer,
destinationLayerColor)
guidResults.append(addJsonFeature(jsonFeature, att))
# return all the guids
return guidResults
def load(rawJsonData,
destinationLayer=None,
destinationLayerColor=System.Drawing.Color.Black):
# if the data already appears to be a dict literal ...
if type(rawJsonData) == dict:
jsonData = rawJsonData
else: # otherwise, just try to load it
jsonData = json.loads(rawJsonData)
# if this is just a GeoJSON ...
if jsonData["type"] == "FeatureCollection":
# process the GeoJSON, pass the layer and color in
return processGeoJson(jsonData, destinationLayer,
destinationLayerColor)
# or if this is a set of layers from PostSites ...
elif jsonData["type"] == "LayerCollection":
# make a list for all the guids
allResults = []
layersList = jsonData['layers']
for layer in layersList: # for each layer
name = layer['name'] # get the name
if 'color' in layer: # get the color if it exists
color = layer['color']
else:
color = destinationLayerColor # or just make it black
geoJson = layer['contents'] # get the GeoJSON for this layer
# make it
layerResults = processGeoJson( geoJson, name, color )
allResults.append(layerResults)
return allResults
else:
return "This doesn't look like correctly formatted GeoJSON data.\nI'm not sure what to do with it, sorry."
