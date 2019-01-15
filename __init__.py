bl_info = {
    "name": "unregis AddOn",
    "author": "unregi Resident",
    "description": "Tools for merging and simplifying multiple objects to fit OpenSim / sl",
    "version": (0, 2),
    "category": "Mesh",
    "blender": (2, 80, 0),
}

import bpy
if bpy.app.version < (2, 80):
    from .unregis_addon_279 import *
else:
    from .unregis_addon_280 import *
