bl_info = {
    "name": "Lenticular",
    "author": "Your Name",
    "version": (1, 1, 0),
    "blender": (4, 2, 0),
    "location": "View3D > Sidebar > Lenticular",
    "description": "Combine multiple images into a lenticular print",
    "category": "Object",
}

import bpy
from . import operators
import importlib

importlib.reload(operators)

# Registration list

classes = (
    operators.lent_load_main,
    operators.lent_main_panel,
    operators.lent_create_material,
    operators.lent_create_lens
)

#Register on add-on load/unload

def register():
    for cls in classes:
        bpy.utils.register_class(cls)

    # Sliders values
    bpy.types.Scene.band_width = bpy.props.FloatProperty(
        name="Band Width (mm)",
        description="Controls image strip width (mm)",
        default=6,
        min = 0.1,
        max = 10)

    bpy.types.Scene.lens_radius = bpy.props.FloatProperty(
        name="Lens Radius (mm)",
        description="Smaller radius makes a smaller field of view",
        default=6,
        min=0.1,
        max=10)

    bpy.types.Scene.lens_thickness = bpy.props.FloatProperty(
        name="Lens Thickness (mm)",
        description="Lens thickness shifts the image focus",
        default=4,
        min=0.1,
        max=10)

    bpy.types.Scene.ior = bpy.props.FloatProperty(
        name="Index of Refraction",
        description="Index of refraction",
        default=1.5,
        min=0.5,
        max=5)

    # Scene-wide variables
    bpy.types.Scene.import_dir = bpy.props.StringProperty(
        name="Import Directory",
        description="Directory for imported files",
        subtype='DIR_PATH'
    )

    bpy.types.Scene.import_f = bpy.props.CollectionProperty(
        name="Imported Files",
        type=bpy.types.OperatorFileListElement
    )

def unregister():
    # Apparently reversing on unload is standard practice
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)


if __name__ == "__main__":
    register()


