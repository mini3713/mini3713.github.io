import rhinoscriptsyntax as rs
import sys
rp_scripts = "rhinopythonscripts"
sys.path.append(rp_scripts)
import rhinopythonscripts

from rhinopythonscripts import GeoJson2Rhino as geojson
g = open('C:/Users/JUWANHA/Desktop/LSM/2021/Study/Seoul/sample.geojson').read()
gj_data = geojson.load(g)
