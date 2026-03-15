import bpy

class lenticular_base(bpy.types.Operator):
    """Add a cube at the 3D cursor"""
    bl_idname = "lent.add_cube"
    bl_label = "Add Cube at Cursor"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        bpy.ops.mesh.primitive_cube_add(location=context.scene.cursor.location)
        self.report({"INFO"}, "Cube added at cursor!")
        return {"FINISHED"}


# N-panel display:

class main_panel(bpy.types.Panel):
    bl_label = "Lenticular Generator"
    bl_idname = "lent_main_panel"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Lenticular"   # Tab label in the sidebar

    def draw(self, context):
        layout = self.layout

        layout.label(text="Use several images to create a lenticular image")
        layout.separator()

        layout.operator("myext.add_cube", icon="MESH_CUBE")