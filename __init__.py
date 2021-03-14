# Export Blender curves to maya v1.0
# Author: Mario Baldi
# web:    www.mariobaldi.com
# email:  info@mariobaldi.com
# Tested on Blender 2.62

import bpy
import mathutils
import re
import math


bl_info = {
    "name": "Autodesk Maya curves",
    "author": "Mario Baldi,(Sav Martin 2.9x port)",
    "blender": (2,90,0),
    "location": "File > Import-Export",
    "description": "Import-Export ma, curves" ,
    "warning": "",
    "wiki_url": "",
    "tracker_url": "",
    "support": 'OFFICIAL',
    "category": "Import-Export"}

def build_maya_matrix():
    maya_mtrx = mathutils.Matrix()
    maya_mtrx[0].xyz = 1.0, 0.0, 0.0
    maya_mtrx[1].xyz = 0.0, 0.0, 1.0
    maya_mtrx[2].xyz = 0.0, -1.0, 0.0
    maya_mtrx[3].xyz = 0.0, 0.0, 0.0
    return maya_mtrx

def build_knots_array(nverts, degree):
    knotLen = nverts + degree - 1
    # These knot values are generated for non-periodic curve. See the maya documentation
    # It will need a fix for closed curves
    # Furthermore, I will build the curve setting the maya minmaxvalue range [0..nspans]
    lastKnotValue = nverts - degree
    kn = []

    for i in range (knotLen):
        v = i-degree+1
        if v<0:
            v=0
        elif v>lastKnotValue or i>=knotLen-degree  :
            v = lastKnotValue

        # Add value to the knot list
        kn.append(v)
    return kn

def write_curve_shape(spline, mtrx=None):
    # Note that BEZIER curves are actually exported as NURBS curves
    # and this script could be extended to properly support them
    if spline.type=="POLY":
        points = spline.points
        degree = 1

    elif spline.type=="BEZIER":
        points = spline.bezier_points
        degree = 3

    elif spline.type=="NURBS":
        points = spline.points
        degree = spline.order_u

    nverts = spline.point_count_u  

    nspans = nverts-degree
    #if degree>1:
    #    nspans -= degree

    knots = build_knots_array(nverts,degree)                   
    nknots = len(knots)
    knots_str = ' '.join(map(str, knots))

    openclosed = 0
    if spline.use_cyclic_u:
        openclosed = 2

    print(knots)
    print(nverts)
    print(nspans)
    print(openclosed)

    curve_attrs = []
    curve_attrs.append('    setAttr -k off ".v"; \n' )
    curve_attrs.append('    setAttr ".cc" -type "nurbsCurve" \n' )
    curve_attrs.append('        %s %s %s no 3 \n' %(degree,nspans,openclosed) ) # I suppose [degree, spans, ? 0:open 2:closed , no(constant), 3(constant)]
    curve_attrs.append('        %s %s   \n' % (nknots, knots_str) ) # Knots array
    curve_attrs.append('        %s \n' % nverts ) #n vertices 

    maya_mtrx = build_maya_matrix()

    if mtrx is not None:
        # When a matrix is supplied, this will be baked to the vertices
        for pt in points:
            t_vec = mathutils.Vector((mtrx[0][3], mtrx[2][3],-mtrx[1][3], 0.0)) 
            wpt = (maya_mtrx @ mtrx) @ pt.co + t_vec
            curve_attrs.append('        %s %s %s \n' %(wpt[0], wpt[1], wpt[2]) )
    else:
        #Using the local verts coordinates
        for pt in points:
            pt = maya_mtrx @ pt.co
            curve_attrs.append('        %s %s %s \n' %(pt[0], pt[1], pt[2]) )

    curve_attrs.append('        ; \n')

    return curve_attrs




def export_curves_to_maya(operator,
         context, filepath="",
         use_selection=True,
         global_matrix=None,
         bake_world_position=True,
         ):

    # This function will export blender curves to .ma maya file format

    # By default, I will export all curves in the scene
    if use_selection:
        selection = bpy.context.selected_objects
    else:
        selection = list(bpy.data.objects)

    #cube = bpy.data.objects["Cube"]
    #print (selection)
    #print(dir(cube))
    #print (type(cube))

    if len(selection)>0:
        # Currently the script doesn't check the UNIT system used
        maya_file_header = []
        maya_file_header.append('//Maya ASCII 2009 scene \n')
        maya_file_header.append('requires maya "2009"; \n')
        maya_file_header.append('currentUnit -l centimeter -a degree -t film; \n')
        maya_file_header.append('fileInfo "application" "maya";\n')
        maya_file_header.append('fileInfo "product" "Maya Unlimited 2009"; \n')
        maya_file_header.append('fileInfo "version" "2009"; \n')

        maya_file = []
        maya_file.extend(maya_file_header)

        for sel in selection:
            #print (type(sel))
            #print (sel.type)
            if sel.type=="MESH":
                # Here I could convert polylines to maya curves (degree=1)
                pass
                '''
                # Some garbage while testing blender scripting... This is my first script after all!!!
                print (sel.name)
                #seldata = bpy.data.meshes[sel.name]   # data by name
                seldata = sel.data
                print (seldata)
                verts = list(seldata.vertices)
                faces = list(seldata.faces)
                print (len(verts))
                print ('\n')
                print (len(faces))
                '''
            if sel.type=="CURVE":
                print (sel.name)
                seldata = sel.data
                print (seldata)

                bake_mw=None
                if bake_world_position:
                    bake_mw = sel.matrix_world
                #print (list(seldata.splines))
    
                ill_chars = [',', '!', '.', ';', '?']
                curves_grp = sel.name
                curves_grp = re.sub('[%s]' % ''.join(ill_chars), '_', curves_grp) # Removing illegal chars
                maya_file.append('createNode transform -n "%s"; \n' % curves_grp)


                for id, spl in enumerate(seldata.splines):
                    # Create curve nodes (transform + shape)
                    curve_t_name = '%s_curve%s' % (sel.name,id+1)
                    curve_shape_name = '%s_curveShape%s' % (sel.name,id+1)
                    # I filter the names to be sure that there aren't illegal characters
                    curve_t_name = re.sub('[%s]' % ''.join(ill_chars), '_', curve_t_name)
                    curve_shape_name = re.sub('[%s]' % ''.join(ill_chars), '_', curve_shape_name)
                    maya_file.append('createNode transform -n "%s" -p "%s"; \n' % (curve_t_name, curves_grp) )
                    maya_file.append('createNode nurbsCurve -n "%s" -p "%s"; \n' % (curve_shape_name, curve_t_name) )

                    # Set Shape Attributes
                    maya_file.extend( write_curve_shape(spl,bake_mw) )

                '''    
                # This part should transform items containing curves (groups) in maya, according the
                # blender selected item world matrix. Sadly I wasn't able to let it work properly. 
                if bake_world_position==False:
                    # I will try to export the correct position of the objects containing the curves 
                    # This is currently WRONG, and shouldn't be used
                    # I am setting the items/groups transformation after parenting the guides
                    maya_mtrx = maya_mtrx = build_maya_matrix()
                    mtrx = maya_mtrx * sel.matrix_world 
                    # Translation
                    t = mtrx.translation
                    # Rotation
                    euler_rad = sel.rotation_euler
                    rx = math.degrees(euler_rad.x)
                    ry = math.degrees(euler_rad.y)
                    rz = math.degrees(euler_rad.z)
                    # Scale
                    s = sel.scale

                    #maya_file.append('    setAttr "%s.t" -type "double3" %s %s %s ; \n' %(curves_grp, t.x, t.y, t.z))
                    #maya_file.append('    setAttr "%s.r" -type "double3" %s %s %s ; \n' %(curves_grp, rx, rz, ry))
                    #maya_file.append('    setAttr "%s.s" -type "double3" %s %s %s ; \n' %(curves_grp, s.x, s.y, s.z))
                    maya_file.append('setAttr "%s.xformMatrix" -type "matrix" \n' %(curves_grp))
                    maya_file.append('    %s %s %s %s \n' %(mtrx[0].x, mtrx[1].x, mtrx[2].x, 0))
                    maya_file.append('    %s %s %s %s \n' %(mtrx[0].y, mtrx[1].y, mtrx[2].y, 0))
                    maya_file.append('    %s %s %s %s \n' %(mtrx[0].z, mtrx[1].z, mtrx[2].z, 0))
                    maya_file.append('    %s %s %s %s ; \n' %(t.x, t.y, t.z, 1))
                    
                    print (mtrx[0].x, mtrx[0].y, mtrx[0].z, 0)
                    print (mtrx[1].x, mtrx[1].y, mtrx[1].z, 0)
                    print (mtrx[2].x, mtrx[2].y, mtrx[2].z, 0)

                '''    
                #print (''.join(map(str, maya_file)))

    # Write mode creates a new file or overwrites the existing content of the file. 
    # Write mode will _always_ destroy the existing contents of a file.
    try:
        # This will create a new file or **overwrite an existing file**.
        print (filepath)
        f = open(filepath, "w")
        try:
            f.writelines(maya_file) # Write a sequence of strings to a file
        finally:
            f.close()
    except IOError:
        return {'ERROR'}  

    return {'FINISHED'}   

# ADDON
                
from bpy.props import StringProperty, FloatProperty, BoolProperty, EnumProperty  # interface  
from bpy_extras.io_utils import (ExportHelper,
                                 axis_conversion,
                                 )


class ExportCurvesToMaya(bpy.types.Operator, ExportHelper):
    '''Export curves to Maya file format (.ma)'''
    bl_idname = "export_scene.autodesk_maya_curves"
    bl_label = 'Export curves to maya'

    filename_ext = ".ma"

    use_selection : BoolProperty(
            name="Selection Only",
            description="Export selected objects only",
            default=False,
            )
            
    #bl_options = {'REGISTER'}  # enable undo for the operator.

    def execute(self, context):        # execute() is called by blender when running the operator.
        # The original script
        keywords = self.as_keywords(ignore=("check_existing",))
        return export_curves_to_maya(self, context, **keywords)


def menu_func_export(self, context):
    self.layout.operator(ExportCurvesToMaya.bl_idname, text="Maya curves (.ma)")

def register():
    bpy.utils.register_class(ExportCurvesToMaya) 
    bpy.types.TOPBAR_MT_file_export.append(menu_func_export)

def unregister():
    bpy.utils.unregister_class(ExportCurvesToMaya)
    bpy.types.TOPBAR_MT_file_export.remove(menu_func_export)
