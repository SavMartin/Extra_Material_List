#-------------------------------------------------------------------------------
#                     Extra Material List - Addon for Blender
#
# - Two display options (preview and plain list)
# - Display object and world materials
# - Eliminate duplicates for node groups and materials
#
# Version: 0.2
# Revised: 11.08.2017
# Author: Miki (meshlogic)
#-------------------------------------------------------------------------------
bl_info = {
    "name": "Extra Material List",
    "author": "Miki (meshlogic), Port to 2.9x Sav Martin",
    "category": "Node",
    "description": "An alternative object/world material list for Node Editor.",
    "location": "Node Editor > Tools > Material List",
    "version": (0, 2),
    "blender": (2, 90, 0)
}

import bpy
from bpy.props import *
from bpy.types import Menu, Operator, Panel, UIList
from bpy.app.handlers import persistent


#-------------------------------------------------------------------------------
# UI PANEL - Extra Material List
#------------------------------------------------------------------------------- 
class EXTRAMATERIALLIST_PT_panel(Panel):
    bl_space_type = 'NODE_EDITOR'
    bl_idname = "EXTRAMATERIALLIST_PT_panel"
    bl_space_type = "NODE_EDITOR"
    bl_region_type = "UI"   
    bl_category = "Material List"
    bl_label = "Extra Material List"

    #--- Available only for "shading nodes" render
    @classmethod
    def poll(cls, context):
        space = context.space_data
        valid_trees = ["ShaderNodeTree",]
        if space.type == 'NODE_EDITOR' and space.tree_type in valid_trees:
            return True

    #--- Draw Panel
    def draw(self, context):
        layout = self.layout
        cs = context.scene
        sdata = context.space_data
        props = cs.extra_material_list
        
        #--- Shader tree and type selection
        row = layout.row()
        row.alignment = 'CENTER'
        # row.prop(sdata, "tree_type", text="", expand=True)
        row.prop(sdata, "shader_type", text="", expand=True)
        
        #--- Proceed only for OBJECT/WORLD shader node trees
        if sdata.tree_type != 'ShaderNodeTree' or (sdata.shader_type != 'OBJECT' and sdata.shader_type != 'WORLD'):
            return
        
        #--- List style buttons
        row = layout.row()
        row.prop(props, "style", expand=True)

        #-----------------------------------------------------------------------        
        # PREVIEW Style
        #-----------------------------------------------------------------------
        if props.style == 'PREVIEW':
        
            #--- Num. of rows & cols for the preview list
            row = layout.row()
            split = row.split(factor=0.6)
            col = split.column(align=True)
            col.prop(props, "rows")
            col.prop(props, "cols")
            
            #--- Object materials
            if sdata.shader_type == 'OBJECT':
                
                # List of all scene materials
                mat_list = bpy.data.materials
                
                # Current active material
                if hasattr(sdata.id_from, "active_material"):
                    mat = sdata.id_from.active_material
                else:
                    return
                
                # Navigation button PREV
                sub = split.column()
                sub.scale_y = 2
                sub.operator("extra_material_list.nav", text="", icon='BACK').dir = 'PREV'
                sub.enabled = enable_prev_button(mat, mat_list)

                # Navigation button NEXT
                sub = split.column()
                sub.scale_y = 2
                sub.operator("extra_material_list.nav", text="", icon='FORWARD').dir = 'NEXT'
                sub.enabled = enable_next_button(mat, mat_list)
                            
                # Preview list
                layout.template_ID_preview(
                    sdata.id_from, "active_material",
                    new = "material.new",
                    rows = props.rows, cols = props.cols
                )

            #--- World materials
            elif sdata.shader_type == 'WORLD':

                # List of all scene worlds
                world_list = bpy.data.worlds

                # Current active world
                world = context.scene.world
                
                # Navigation button PREV
                sub = split.column()
                sub.scale_y = 2
                sub.operator("extra_material_list.nav", text="", icon='BACK').dir = 'PREV'
                sub.enabled = enable_prev_button(world, world_list)
                
                # Navigation button NEXT
                sub = split.column()
                sub.scale_y = 2
                sub.operator("extra_material_list.nav", text="", icon='FORWARD').dir = 'NEXT'
                sub.enabled = enable_next_button(world, world_list)
                
                # Preview list
                layout.template_ID_preview(
                    cs, "world",
                    new = "world.new",
                    rows = props.rows, cols = props.cols
                )
                
            layout.separator()
                
        #-----------------------------------------------------------------------        
        # LIST Style
        #-----------------------------------------------------------------------
        elif props.style == 'LIST':
            
            #--- Object materials
            if sdata.shader_type == 'OBJECT':
                layout.template_list(
                    "EXTRA_MATERIAL_LIST_UL_list", "",
                    bpy.data, "materials",
                    props, "material_id",
                    rows = len(bpy.data.materials)
                )
                
            #--- World materials
            elif sdata.shader_type == 'WORLD':
                layout.template_list(
                    "EXTRA_MATERIAL_LIST_UL_list", "",
                    bpy.data, "worlds",
                    props, "world_id",
                    rows = len(bpy.data.worlds)
                )
            
            #--- Show icons prop
            row = layout.row()
            row.prop(props, "show_icons")
        
        #----------------------------------------------------------------------- 
        # ELIMINATE Duplicates
        #-----------------------------------------------------------------------
        row = layout.row()
        row.label(text="Eliminate Duplicates:", icon='CANCEL')
        row = layout.row(align=True)
        row.operator("extra_material_list.eliminate_nodegroups", text="Node Groups")
        row.operator("extra_material_list.eliminate_materials", text="Materials")
        
        
#-------------------------------------------------------------------------------
# Functions to decide if enable/disable navigation buttons
#------------------------------------------------------------------------------- 
def enable_prev_button(item, item_list):
    if item != None and len(item_list) > 0:
        return item != item_list[0]
    else:
        return False
    
def enable_next_button(item, item_list):
    if item != None and len(item_list) > 0:
        return item != item_list[-1]
    else:
        return False


#-------------------------------------------------------------------------------
# CUSTOM TEMPLATE_LIST FOR MATERIALS
#------------------------------------------------------------------------------- 
class EXTRA_MATERIAL_LIST_UL_list(UIList):
    
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        props = bpy.context.scene.extra_material_list
        
        # Material name and icon
        row = layout.row(align=True)
        if props.show_icons:
            row.prop(item, "name", text="", emboss=False, icon_value=icon)
        else:
            row.prop(item, "name", text="", emboss=False, icon_value=0)
        
        # Material status (fake user, zero users)
        row = row.row(align=True)
        row.alignment = 'RIGHT'
        
        if item.use_fake_user:
            row.label(text="F")
        else:
            if item.users == 0:
                row.label(text="0")


#--- Update the active material when you select another item in the template_list
def update_active_material(self, context):
    try:
        id = bpy.context.scene.extra_material_list.material_id
        if id < len(bpy.data.materials):
            mat = bpy.data.materials[id]
            bpy.context.object.active_material = mat
    except:
        pass

#--- Update the active world shader when you select another item in the template_list
def update_active_world(self, context):
    try:
        id = bpy.context.scene.extra_material_list.world_id
        if id < len(bpy.data.worlds):
            world = bpy.data.worlds[id]
            bpy.context.scene.world = world
    except:
        pass  

#-------------------------------------------------------------------------------
# ELIMINATE MATERIAL DUPLICATES
#-------------------------------------------------------------------------------     
class ExtraMaterialList_OT_EliminateMaterials(Operator):
    bl_idname = "extra_material_list.eliminate_materials"
    bl_label = "Eliminate Material Duplicates"
    bl_description = "Eliminate material duplicates (ending with .001, .002, etc) and replace them with the original material if found."
    
    def execute(self, context):
        print("\nEliminate Material Duplicates:")
        mats = bpy.data.materials
                
        #--- Search for mat. slots in all objects
        for obj in bpy.data.objects:
            for slot in obj.material_slots:
                
                # Get the material name as 3-tuple (base, separator, extension)
                (base, sep, ext) = slot.name.rpartition('.')
                
                # Replace the numbered duplicate with the original if found
                if ext.isnumeric():
                    if base in mats:
                        print("  For object '%s' replace '%s' with '%s'" % (obj.name, slot.name, base))
                        slot.material = mats.get(base)

        return{'FINISHED'}

#-------------------------------------------------------------------------------
# ELIMINATE NODE GROUP DUPLICATES
#-------------------------------------------------------------------------------
class ExtraMaterialList_OT_EliminateNodeGroups(Operator):
    bl_idname = "extra_material_list.eliminate_nodegroups"
    bl_label = "Eliminate Node Group Duplicates"
    bl_description = "Eliminate node group duplicates (ending with .001, .002, etc) and replace them with the original node group if found."
    
    #--- Eliminate node group duplicate with the original group found
    def eliminate(self, node):
        node_groups = bpy.data.node_groups
        
        # Get the node group name as 3-tuple (base, separator, extension)
        (base, sep, ext) = node.node_tree.name.rpartition('.')
        
        # Replace the numbered duplicate with original if found
        if ext.isnumeric():
            if base in node_groups:
                print("  Replace '%s' with '%s'" % (node.node_tree.name, base))
                node.node_tree.use_fake_user = False
                node.node_tree = node_groups.get(base)
        
    #--- Execute
    def execute(self, context):
        print("\nEliminate Node Group Duplicates:")
        
        mats = list(bpy.data.materials)
        worlds = list(bpy.data.worlds)
        node_groups = bpy.data.node_groups
        
        #--- Search for duplicates in the actual node groups
        for group in node_groups:
            for node in group.nodes:
                if node.type == 'GROUP':
                    self.eliminate(node)
                    
        #--- Search for duplicates in materials
        for mat in mats + worlds:
            if mat.use_nodes:
                for node in mat.node_tree.nodes:
                    if node.type == 'GROUP':
                        self.eliminate(node)
                            
        return{'FINISHED'}

#-------------------------------------------------------------------------------
# NAVIGATION OPERATOR
#------------------------------------------------------------------------------- 
class ExtraMaterialList_OT_Nav(Operator):
    bl_idname = "extra_material_list.nav"
    bl_label = "Nav"
    bl_description = "Navigation button"

    dir : EnumProperty(
        items = [
            ('NEXT', "PREV", "PREV"),
            ('PREV', "PREV", "PREV")
        ],
        name = "dir",
        default = 'NEXT')

    def execute(self, context):
        sdata = context.space_data
        
        #--- Navigate in object materials
        if sdata.shader_type == 'OBJECT':
            
            # List of all scene materials
            mat_list = list(bpy.data.materials)
            
            # Get index of the current active material
            mat = sdata.id_from.active_material
            if mat in mat_list:
                id = mat_list.index(mat)
            else:
                return{'FINISHED'}      
            
            # Navigate
            if self.dir == 'NEXT':
                if id+1 < len(mat_list):
                    sdata.id_from.active_material = mat_list[id+1]

            if self.dir == 'PREV':
                if id > 0:
                    sdata.id_from.active_material = mat_list[id-1]

        #--- Navigate in worlds
        elif sdata.shader_type == 'WORLD':
            
            # List of all scene worlds
            world_list = list(bpy.data.worlds)
            
            # Get index of the current active world
            world = context.scene.world
            if world in world_list:
                id = world_list.index(world)
            else:
                return{'FINISHED'}      
            
            # Navigate
            if self.dir == 'NEXT':
                if id+1 < len(world_list):
                    context.scene.world = world_list[id+1]

            if self.dir == 'PREV':
                if id > 0:
                    context.scene.world = world_list[id-1]

        return{'FINISHED'}


#-------------------------------------------------------------------------------
# CUSTOM HANDLER (scene_update_post)
# - This handler is invoked after the scene updates
# - Keeps template_list synced with the active material
#-------------------------------------------------------------------------------
@persistent
def update_material_list(context):
    try:
        props = bpy.context.scene.extra_material_list
        
        #--- Update world list
        try:
            world = bpy.context.scene.world
            if world != None:
                id = bpy.data.worlds.find(world.name)
                if id != -1 and id != props.world_id:
                    props.world_id = id
        except:
            pass    
        
        #--- Update material list
        try:
            mat = bpy.context.object.active_material
            if mat != None:
                id = bpy.data.materials.find(mat.name)
                if id != -1 and id != props.material_id:
                    props.material_id = id
        except:
            pass
    except:
        pass


#-------------------------------------------------------------------------------
# CUSTOM SCENE PROPS
#-------------------------------------------------------------------------------        
class ExtraMaterialList_Props(bpy.types.PropertyGroup):
        
    style : EnumProperty(
        items = [
            ('PREVIEW', "Preview", "", 0),
            ('LIST', "List", "", 1),
        ],
        default = 'PREVIEW',
        name = "Style",
        description = "Material list style")
    
    rows : IntProperty(
        name = "Rows",
        description = "Num. of rows in the preview list",
        default = 5, min = 1, max = 15)
        
    cols : IntProperty(
        name = "Cols",
        description = "Num. of columns in the preview list",
        default = 10, min = 1, max = 30)
    
    # Index of the active material in the template_list
    material_id : IntProperty(
        default = 0,
        update = update_active_material)
    
    # Index of the active world in the template_list
    world_id : IntProperty(
        default = 0,
        update = update_active_world)

    show_icons : BoolProperty(
        name = "Show material icons",
        default = False)
        

#-------------------------------------------------------------------------------
# REGISTER/UNREGISTER ADDON CLASSES
#-------------------------------------------------------------------------------
classes = (
    EXTRAMATERIALLIST_PT_panel,
    ExtraMaterialList_OT_Nav,
    ExtraMaterialList_OT_EliminateNodeGroups,
    ExtraMaterialList_OT_EliminateMaterials,
    EXTRA_MATERIAL_LIST_UL_list,
    ExtraMaterialList_Props
)

def register():
    for c in classes:
        bpy.utils.register_class(c)
    bpy.types.Scene.extra_material_list = PointerProperty(type=ExtraMaterialList_Props)
    bpy.app.handlers.depsgraph_update_pre.append(update_material_list)

def unregister():
    for c in classes:
        bpy.utils.unregister_class(c)    
    del bpy.types.Scene.extra_material_list
    bpy.app.handlers.depsgraph_update_post.remove(update_material_list)

if __name__ == "__main__":
    register()
