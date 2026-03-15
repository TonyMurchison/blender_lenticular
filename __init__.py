bl_info = {
    "name": "Lenticular Printing",
    "author": "Wout Verswijveren",
    "version": (1, 1, 0),
    "blender": (4, 2, 0),
    "location": "View3D > Sidebar > Lenticular Generator",
    "description": "A lenticular image and geometry generator",
    "category": "Object",
}

import bpy
from . import operators

# Registration

classes = (
    operators.lenticular_base,
    operators.main_panel,
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)


if __name__ == "__main__":
    register()
