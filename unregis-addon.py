'''
    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.

    Dieses Programm ist Freie Software: Sie können es unter den Bedingungen
    der GNU General Public License, wie von der Free Software Foundation,
    Version 3 der Lizenz oder (nach Ihrer Wahl) jeder neueren
    veröffentlichten Version, weiter verteilen und/oder modifizieren.

    Dieses Programm wird in der Hoffnung bereitgestellt, dass es nützlich sein wird, jedoch
    OHNE JEDE GEWÄHR,; sogar ohne die implizite
    Gewähr der MARKTFÄHIGKEIT oder EIGNUNG FÜR EINEN BESTIMMTEN ZWECK.
    Siehe die GNU General Public License für weitere Einzelheiten.

    Sie sollten eine Kopie der GNU General Public License zusammen mit diesem
    Programm erhalten haben. Wenn nicht, siehe <https://www.gnu.org/licenses/>.
'''
bl_info = {
    "name": "unregis AddOn",
    "author": "unregi Resident",
    "description": "Tools for merging and simplifying multiple objects to fit OpenSim / SL",
    "version": (0, 1),
    "category": "Mesh",
}

import bpy
from bpy.types import Panel

import bmesh
import math
import random

def getTexturesOfObject(object):
    textures = []
    ctx['active_object'] = object
    for matslot in object.material_slots:
        texture = getTextureOfMaterialSlot(matslot)
        print(object.name, 'has material',
            matslot.material.name, 'that uses image',
            texture)
        if texture not in textures:
            textures.append(texture)
    return textures

def getTextureOfMaterialSlot(matslot):
    for texslot in matslot.material.texture_slots:
        if texslot is not None and texslot.texture.type == 'IMAGE':
            if texslot.texture.image is not None:
                return texslot.texture.image.name
                print(object.name, 'has material',
                    matslot.material.name, 'that uses image',
                    texslot.texture.image.name)

class SLMergeMeshes(bpy.types.Operator):
    """Merge slecte objects"""
    bl_idname = "unregi.mergemesh"
    bl_label = "Merge selected objects"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        ctx = context.copy()
        meshlist = [o for o in context.selected_objects if o.type == 'MESH']
        if len(meshlist) <= 1:
            print("No objects to join")
            return {'CANCELLED'}
        #rename UV maps
        salt = str(random.randint(100, 999))
        uvname = 'UVMap' + salt
        for o in meshlist:
            for uvmap in  o.data.uv_layers :
                uvmap.name = uvname
        #join into active object
        ctx['acive_object'] = meshlist[0]
        ctx['selected_objects'] = meshlist
        ctx['selected_editable_bases'] = [context.scene.object_bases[o.name] for o in meshlist]
        bpy.ops.object.join(ctx)
        context.scene.update()
        self.report({'INFO'}, "%d meshes joined" % (len(meshlist),))
        return {'FINISHED'}

class SLMergeMaterials(bpy.types.Operator):
    """Merge Materialslots with same texture"""
    bl_idname = "unregi.mergematslot"
    bl_label = "Merge Material slots that use same textures"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        mobject = context.scene.objects.active 
        textures = []
        slot = 0
        before_nummat = len(mobject.material_slots)
        nummat = len(mobject.material_slots)
        print("Checking " + str(nummat) + " materials for possible merge")
        while slot < nummat:
            if mobject.material_slots[slot].material is None:
                print("No material assigned in slot " + str(slot) + " removing it")
                context.object.active_material_index = slot
                bpy.ops.object.material_slot_remove()
                nummat -= 1
                continue
            texture = getTextureOfMaterialSlot(mobject.material_slots[slot])
            if texture not in textures:
                textures.append(texture)
                slot += 1
            else:
                context.object.active_material_index = slot
                targetslot = textures.index(texture) + 1
                if targetslot != slot:
                    print("Have to move slot " + str(slot) + " to " + str(targetslot))
                    for _ in range(slot - targetslot):
                        bpy.ops.object.material_slot_move(direction='UP')
                print("Merge slot " + str(targetslot) + " with " + str(targetslot - 1))
                bpy.ops.object.material_slot_remove()
                nummat -= 1
        new_nummat = len(mobject.material_slots)
        self.report({'INFO'}, "%d materials merged, %d materials left" % (before_nummat - new_nummat, new_nummat))
        return {'FINISHED'}
    
class SLDeleteUnusedMaterials(bpy.types.Operator):
    """Remove unused Materials"""
    bl_idname = "unregi.remmat"
    bl_label = "Remove Materials that are not used"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        for material in bpy.data.materials:
            if not material.users:
                bpy.data.materials.remove(material)
        return {'FINISHED'}

class SLMaterialsShadeless(bpy.types.Operator):
    """Materials Shadeless"""
    bl_idname = "unregi.shadeless"
    bl_label = "Make all Materials shadeless"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        for item in bpy.data.materials:
            item.use_shadeless = True
        return {'FINISHED'}

class SLCleanup(bpy.types.Operator):
    """CleanUp Objects"""
    bl_idname = "unregi.cleanup"
    bl_label = "Remove Doubles and dissolve degenerates in all selected objects"
    bl_options = {'REGISTER', 'UNDO'}
    distance = bpy.props.FloatProperty(name="Distance", default=0.00001, min=0.000001, max=0.01)

    def execute(self, context):
        objects = [o.data for o in context.selected_objects if o.type == 'MESH']
        num_before = sum(len(m.vertices) for m in objects)
        bm = bmesh.new()
        for o in objects:
            bm.from_mesh(o)
            bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=self.distance)
            bmesh.ops.dissolve_degenerate(bm, edges=bm.edges, dist=self.distance)
            bm.to_mesh(o)
            o.update()
            bm.clear()
        bm.free()
        num_deleted = num_before - sum(len(m.vertices) for m in objects)
        self.report({'INFO'}, "%d from %d vertices removed" % (num_deleted, num_before))
        return {'FINISHED'}

class SLConvexHull(bpy.types.Operator):
    """Convert objects to Convex Hulls"""
    bl_idname = "unregi.convexhull"
    bl_label = "Convert selected objects to Convex Hulls"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        objects = [o for o in context.selected_objects if o.type == 'MESH']
        for obj in objects:
            context.scene.objects.active = obj
            #make convex
            bpy.ops.object.editmode_toggle()
            bpy.ops.mesh.select_all(action='SELECT')
            bpy.ops.mesh.convex_hull()
            bpy.ops.object.editmode_toggle()
            #delete materials
            slot = 0
            nummat = len(obj.material_slots)
            while slot < nummat:
                bpy.ops.object.material_slot_remove()
                slot += 1
        return {'FINISHED'}

class SLMakeTris(bpy.types.Operator):
    """Convert to Triangles"""
    bl_idname = "unregi.maketris"
    bl_label = "Convert selected objects to triangles"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        objects = [o for o in context.selected_objects if o.type == 'MESH']
        for obj in objects:
            context.scene.objects.active = obj
            bpy.ops.object.editmode_toggle()
            bpy.ops.mesh.select_all(action='SELECT')
            bpy.ops.mesh.quads_convert_to_tris()
            bpy.ops.object.editmode_toggle()
        return {'FINISHED'}
    
class SLMakeQuads(bpy.types.Operator):
    """Convert Triangles to Quads"""
    bl_idname = "unregi.makequads"
    bl_label = "Convert selected objects to quads"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        objects = [o for o in context.selected_objects if o.type == 'MESH']
        for obj in objects:
            context.scene.objects.active = obj
            bpy.ops.object.editmode_toggle()
            bpy.ops.mesh.select_all(action='SELECT')
            bpy.ops.mesh.tris_convert_to_quads()
            bpy.ops.object.editmode_toggle()
        return {'FINISHED'}

class SLPlanarDecimate(bpy.types.Operator):
    """Planar Decimate Objects"""
    bl_idname = "unregi.planardec"
    bl_label = "Planar Decimate over selected objects"
    bl_options = {'REGISTER', 'UNDO'}
    angle = bpy.props.IntProperty(name="Max Angle", default=5, min=0, max=25)

    def cleanAllDecimateModifiers(self, obj):
        for m in obj.modifiers:
            if(m.type=="DECIMATE"):
                obj.modifiers.remove(modifier=m)

    def execute(self, context):
        ctx = context.copy()
        objects = [o for o in context.selected_objects if o.type == 'MESH']
        modifiers = []
        modifierName='DecimateMod'
        for o in objects:
            self.cleanAllDecimateModifiers(o)
            ctx['acive_object'] = o
            modifier= o.modifiers.new(modifierName,'DECIMATE')
            modifier.decimate_type = 'DISSOLVE'
            modifier.angle_limit = self.angle * 2 * math.pi / 360
            print("Planar decimate of mesh " + o.name + " by " + str(modifier.angle_limit))
            bpy.ops.object.modifier_apply(modifier=modifier.name)
        return {'FINISHED'}
        context.scene.update()

class SLDecimate(bpy.types.Operator):
    """Decimate Objects"""
    bl_idname = "unregi.decimate"
    bl_label = "Decimate over selected objects"
    bl_options = {'REGISTER', 'UNDO'}
    ratio = bpy.props.FloatProperty(name="Ratio", default=0.2, min=0.0, max=1.0)

    def cleanAllDecimateModifiers(self, obj):
        for m in obj.modifiers:
            if(m.type=="DECIMATE"):
                obj.modifiers.remove(modifier=m)

    def execute(self, context):
        ctx = context.copy()
        objects = [o for o in context.selected_objects if o.type == 'MESH']
        modifiers = []
        modifierName='DecimateMod'
        for o in objects:
            self.cleanAllDecimateModifiers(o)
            ctx['acive_object'] = o
            modifier= o.modifiers.new(modifierName,'DECIMATE')
            modifier.decimate_type = 'COLLAPSE'
            modifier.ratio = self.ratio
            print("Decimate of mesh " + o.name + " by " + str(modifier.ratio))
            bpy.ops.object.modifier_apply(modifier=modifier.name)
        return {'FINISHED'}
        context.scene.update()

class UnregisPanel(Panel):
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'TOOLS'
    bl_label = 'unregis Tools'
    bl_context = 'objectmode'
    bl_category = 'Tools'

    def draw(self, context):
        layout = self.layout
        layout.label(text='View', icon='PARTICLEMODE')
        layout.operator('unregi.shadeless', text='Make Materials Shadeless')
        layout.operator('unregi.remmat', text='Remove unused Materials')
        layout.label(text='Merge', icon='MOD_SOLIDIFY')
        layout.operator('unregi.mergemesh', text='Merge Objects')
        layout.operator('unregi.mergematslot', text='Merge Same Materials')
        layout.label(text='Physics Shape', icon='MESH_ICOSPHERE')
        layout.operator('unregi.convexhull', text='Create Convex Hulls')
        layout.operator('unregi.decimate', text='Decimate')
        layout.label(text='CleanUp', icon='MOD_WAVE')
        layout.operator('unregi.cleanup', text='Remove Doubles and Degenerates')
        layout.operator('unregi.planardec', text='Planar Decimate')
        layout.operator('unregi.maketris', text='Convert to Triangles')
        layout.operator('unregi.makequads', text='Triangles to Quads')

def register():
    bpy.utils.register_class(SLMaterialsShadeless)
    bpy.utils.register_class(SLMakeTris)
    bpy.utils.register_class(SLMakeQuads)
    bpy.utils.register_class(SLCleanup)
    bpy.utils.register_class(SLPlanarDecimate)
    bpy.utils.register_class(SLMergeMaterials)
    bpy.utils.register_class(SLDeleteUnusedMaterials)
    bpy.utils.register_class(SLMergeMeshes)
    bpy.utils.register_class(SLConvexHull)
    bpy.utils.register_class(SLDecimate)
    bpy.utils.register_class(UnregisPanel)

def unregister():
    bpy.utils.unregister_class(SLMaterialsShadeless)
    bpy.utils.unregister_class(SLMakeTris)
    bpy.utils.unregister_class(SLMakeQuads)
    bpy.utils.unregister_class(SLCleanup)
    bpy.utils.unregister_class(SLPlanarDecimate)
    bpy.utils.unregister_class(SLMergeMaterials)
    bpy.utils.unregister_class(SLDeleteUnusedMaterials)
    bpy.utils.unregister_class(SLMergeMeshes)
    bpy.utils.unregister_class(SLConvexHull)
    bpy.utils.unregister_class(SLDecimate)
    bpy.utils.unregister_class(UnregisPanel)

if __name__ == '__main__':
    register()

