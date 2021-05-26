import rhinoscriptsyntax as rs
import sys
rp_scripts = "rhinopythonscripts"
sys.path.append(rp_scripts)
import rhinopythonscripts

from rhinopythonscripts import GeoJson2Rhino as geojson
g = open('d:/temp/sample.geojson').read()
gj_data = geojson.load(g)
