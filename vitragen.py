# Nikita Akimov
# interplanety@interplanety.org
#
# GitHub
#    https://github.com/Korchy/1d_vitragen

import bmesh
import bpy
from bpy.props import FloatProperty
from bpy.types import Operator, Panel, Scene
from bpy.utils import register_class, unregister_class
from mathutils import Vector

bl_info = {
    "name": "Vitragen",
    "description": "Generates frames (imposters) for stained-glass windows",
    "author": "Nikita Akimov, Paul Kotelevets",
    "version": (1, 0, 0),
    "blender": (2, 79, 0),
    "location": "View3D > Tool panel > 1D > Vertical Vertices",
    "doc_url": "https://github.com/Korchy/1d_vitragen",
    "tracker_url": "https://github.com/Korchy/1d_vitragen",
    "category": "All"
}


# MAIN CLASS

class Vitragen:

    _threshold = 0.01

    @classmethod
    def generate_imposters(cls, context, src_obj, hiw=1.0, how=1.0, viw=1.0, vow=1.0):
        # generate frames (imposters) for src_obj
        # current mode
        mode = src_obj.mode
        # switch to OBJECT mode
        if src_obj.mode == 'EDIT':
            bpy.ops.object.mode_set(mode='OBJECT')
        # make different objects by different types of edges loops
        obj_hi = cls._loop_obj(context=context, src_obj=src_obj, name='hi')
        obj_ho = cls._loop_obj(context=context, src_obj=src_obj, name='ho')
        obj_vi = cls._loop_obj(context=context, src_obj=src_obj, name='vi')
        obj_vo = cls._loop_obj(context=context, src_obj=src_obj, name='vo')
        # convert meshes to curves
        cls._object_to_curve(obj=obj_hi)
        cls._object_to_curve(obj=obj_ho)
        cls._object_to_curve(obj=obj_vi)
        cls._object_to_curve(obj=obj_vo)
        # create bevel curves for each type of loop
        bevel_hi = cls._bevel_obj(context=context, name='hi', width=hiw)
        obj_hi.data.bevel_object = bevel_hi
        obj_hi.data.use_fill_caps = True
        bevel_ho = cls._bevel_obj(context=context, name='ho', width=how)
        obj_ho.data.bevel_object = bevel_ho
        obj_ho.data.use_fill_caps = True
        bevel_vi = cls._bevel_obj(context=context, name='vi', width=viw)
        obj_vi.data.bevel_object = bevel_vi
        obj_vi.data.use_fill_caps = True
        bevel_vo = cls._bevel_obj(context=context, name='vo', width=vow)
        obj_vo.data.bevel_object = bevel_vo
        obj_vo.data.use_fill_caps = True
        # return mode back
        bpy.ops.object.mode_set(mode=mode)

    @staticmethod
    def _object_to_curve(obj):
        # convert object to curve
        bpy.ops.object.select_all(action='DESELECT')
        obj.select = True
        bpy.context.scene.objects.active = obj
        bpy.ops.object.convert(target='CURVE')

    @classmethod
    def _loop_obj(cls, context, src_obj, name):
        # create object by required type of edge loops
        # name - type of loops: hi/ho/vi/vo
        # make a copy of src_obj
        new_obj = src_obj.copy()
        new_obj.data = src_obj.data.copy()
        # rename my loop type
        new_obj.name = name     # hi/ho/vi/vo
        context.scene.objects.link(new_obj)
        # in bmesh remove edges that not corresponds loop type
        bm = bmesh.new()
        bm.from_mesh(new_obj.data)
        bm.edges.ensure_lookup_table()
        for e in [edge for edge in bm.edges if not getattr(cls, '_is_edge_' + name)(edge=edge)]:
            bm.edges.remove(e)
        # save edited data to mesh
        bm.to_mesh(new_obj.data)
        # apply transforms
        bpy.ops.object.transform_apply(rotation=True, scale=True)
        # return pointer to the mesh
        return new_obj

    @classmethod
    def _bevel_obj(cls, context, name, width):
        # create rectangle curve for bevel
        curve_data = context.blend_data.curves.new(name='bevel_' + name, type='CURVE')
        curve_obj = context.blend_data.objects.new(name='bevel_' + name, object_data=curve_data)
        context.scene.objects.link(curve_obj)
        spline = curve_data.splines.new('POLY')
        spline.use_cyclic_u = True
        verts = [
            Vector((-width/2, width/2, 0.0)),
            Vector((width/2, width/2, 0.0)),
            Vector((width/2, -width/2, 0.0)),
            Vector((-width/2, -width/2, 0.0))
        ]
        spline.points.add(len(verts) - 1)
        for i, coord in enumerate(verts):
            x, y, z = coord
            spline.points[i].co = (x, y, z, 1)
        return curve_obj

    @classmethod
    def _is_edge_hi(cls, edge):
        # check if edge is horizontal inner
        if abs(edge.verts[0].co.z - edge.verts[1].co.z) < cls._threshold \
                and len(edge.link_faces) > 1:
            return True
        else:
            return False

    @classmethod
    def _is_edge_ho(cls, edge):
        # check if edge is horizontal outer
        if abs(edge.verts[0].co.z - edge.verts[1].co.z) < cls._threshold \
                and len(edge.link_faces) == 1:
            return True
        else:
            return False

    @classmethod
    def _is_edge_vi(cls, edge):
        # check if edge is vertical inner
        if abs(edge.verts[0].co.x - edge.verts[1].co.x) < cls._threshold \
                and abs(edge.verts[0].co.y - edge.verts[1].co.y) < cls._threshold \
                and len(edge.link_faces) > 1:
            return True
        else:
            return False

    @classmethod
    def _is_edge_vo(cls, edge):
        # check if edge is vertical outer
        if abs(edge.verts[0].co.x - edge.verts[1].co.x) < cls._threshold \
                and abs(edge.verts[0].co.y - edge.verts[1].co.y) < cls._threshold \
                and len(edge.link_faces) == 1:
            return True
        else:
            return False


# OPERATORS

class Vitragen_OT_generate_imposters(Operator):
    bl_idname = 'vitragen.generate_imposters'
    bl_label = 'Generate Imposters'
    bl_description = 'Generate Imposters'
    bl_options = {'REGISTER', 'UNDO'}

    width_hi = FloatProperty(
        name='Horizontal Inner Width',
        default=0.2,
        min=0.0
    )

    width_ho = FloatProperty(
        name='Horizontal Outer Width',
        default=0.2,
        min=0.0
    )

    width_vi = FloatProperty(
        name='Vertical Inner Width',
        default=0.2,
        min=0.0
    )

    width_vo = FloatProperty(
        name='Vertical Outer Width',
        default=0.2,
        min=0.0
    )

    def execute(self, context):
        Vitragen.generate_imposters(
            context=context,
            src_obj=context.active_object,
            hiw=self.width_hi,
            how=self.width_ho,
            viw=self.width_vi,
            vow=self.width_vo
        )
        return {'FINISHED'}


# PANELS

class Vitragen_PT_panel(Panel):
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'TOOLS'
    bl_label = 'Vitragen'
    bl_category = '1D'

    def draw(self, context):
        layout = self.layout
        op = layout.operator(
            operator='vitragen.generate_imposters',
            icon='GRID'
        )
        op.width_hi = context.scene.vitragen_width_hi
        op.width_ho = context.scene.vitragen_width_ho
        op.width_vi = context.scene.vitragen_width_vi
        op.width_vo = context.scene.vitragen_width_vo
        # props
        layout.prop(
            data=context.scene,
            property='vitragen_width_hi'
        )
        layout.prop(
            data=context.scene,
            property='vitragen_width_ho'
        )
        layout.prop(
            data=context.scene,
            property='vitragen_width_vi'
        )
        layout.prop(
            data=context.scene,
            property='vitragen_width_vo'
        )


# REGISTER

def register():
    Scene.vitragen_width_hi = FloatProperty(
        name='Horizontal Inner Width',
        default=0.2,
        min=0.0
    )
    Scene.vitragen_width_ho = FloatProperty(
        name='Horizontal Outer Width',
        default=0.2,
        min=0.0
    )
    Scene.vitragen_width_vi = FloatProperty(
        name='Vertical Inner Width',
        default=0.2,
        min=0.0
    )
    Scene.vitragen_width_vo = FloatProperty(
        name='Vertical Outer Width',
        default=0.2,
        min=0.0
    )
    register_class(Vitragen_OT_generate_imposters)
    register_class(Vitragen_PT_panel)


def unregister():
    unregister_class(Vitragen_PT_panel)
    unregister_class(Vitragen_OT_generate_imposters)
    del Scene.vitragen_width_hi
    del Scene.vitragen_width_ho
    del Scene.vitragen_width_vi
    del Scene.vitragen_width_vo


if __name__ == "__main__":
    register()
