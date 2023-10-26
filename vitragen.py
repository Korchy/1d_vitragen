# Nikita Akimov
# interplanety@interplanety.org
#
# GitHub
#    https://github.com/Korchy/1d_vitragen

import bmesh
import bpy
from bpy.props import BoolProperty, EnumProperty, FloatProperty
from bpy.types import Operator, Panel, Scene
from bpy.utils import register_class, unregister_class
from mathutils import kdtree, Vector

bl_info = {
    "name": "Vitragen",
    "description": "Generates frames (imposters) for stained-glass windows",
    "author": "Nikita Akimov, Paul Kotelevets",
    "version": (1, 2, 3),
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
    def generate_imposters(cls, context, src_obj, hiw=1.0, how=1.0, viw=1.0, vow=1.0, rotate_v_imposters='None',
                           reuse_bevel_objects=False):
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
        obj_hi = cls._object_to_curve(context=context, obj=obj_hi)
        obj_ho = cls._object_to_curve(context=context, obj=obj_ho)
        obj_vi = cls._object_to_curve(context=context, obj=obj_vi)
        obj_vo = cls._object_to_curve(context=context, obj=obj_vo)
        # correct imposters tilt
        if rotate_v_imposters != 'None':
            if obj_vi and obj_vi.type == 'CURVE':
                cls._correct_tilt(context=context, src_obj=src_obj, obj=obj_vi, obj_name='vi', rotate_v_imposters=rotate_v_imposters)
            if obj_vo and obj_vo.type == 'CURVE':
                cls._correct_tilt(context=context, src_obj=src_obj, obj=obj_vo, obj_name='vo', rotate_v_imposters=rotate_v_imposters)
        # create bevel curves for each type of loop
        if obj_hi and obj_hi.type == 'CURVE':
            bevel_hi = cls._bevel_obj(context=context, name='hi', width=hiw, reuse_bevel_objects=reuse_bevel_objects)
            obj_hi.data.bevel_object = bevel_hi
            obj_hi.data.use_fill_caps = True
        if obj_ho and obj_ho.type == 'CURVE':
            bevel_ho = cls._bevel_obj(context=context, name='ho', width=how, reuse_bevel_objects=reuse_bevel_objects)
            obj_ho.data.bevel_object = bevel_ho
            obj_ho.data.use_fill_caps = True
        if obj_vi and obj_vi.type == 'CURVE':
            bevel_vi = cls._bevel_obj(context=context, name='vi', width=viw, reuse_bevel_objects=reuse_bevel_objects)
            obj_vi.data.bevel_object = bevel_vi
            obj_vi.data.use_fill_caps = True
        if obj_vo and obj_vo.type == 'CURVE':
            bevel_vo = cls._bevel_obj(context=context, name='vo', width=vow, reuse_bevel_objects=reuse_bevel_objects)
            obj_vo.data.bevel_object = bevel_vo
            obj_vo.data.use_fill_caps = True
        # return mode back
        context.scene.objects.active = src_obj
        bpy.ops.object.mode_set(mode=mode)

    @staticmethod
    def _object_to_curve(context, obj):
        # convert object to curve
        bpy.ops.object.select_all(action='DESELECT')
        obj.select = True
        context.scene.objects.active = obj
        bpy.ops.object.convert(target='CURVE')
        if obj.type != 'CURVE':
            # can't convert to curve - remove
            context.blend_data.objects.remove(obj, do_unlink=True)
            return None
        return obj

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
    def _bevel_obj(cls, context, name, width, reuse_bevel_objects=False):
        # create rectangle curve for bevel
        curve_obj = None
        if reuse_bevel_objects:
            # try to use already created bevel objects
            curve_obj = next((obj for obj in context.blend_data.objects
                              if obj.type == 'CURVE' and obj.name == 'bevel_' + name), None)
        if curve_obj is None:
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
    def _correct_tilt(cls, context, src_obj, obj, obj_name, rotate_v_imposters='None'):
        # correct tilt - curve rotation around its axis on angle = normal rotation in its points
        # crete kdtree for quick finding nearest vertices
        size = len(src_obj.data.vertices)
        kd = kdtree.KDTree(size)
        # for i, v in enumerate(selected_vertices):
        for v in src_obj.data.vertices:
            kd.insert(Vector((v.co.x, v.co.y, v.co.z)), v.index)
        kd.balance()
        # process imposters object
        for spline in obj.data.splines:
            # for point in spline.points:
            point = spline.points[0]
            # find nearest point in src_obj
            nearest = kd.find_range(
                co=Vector((point.co.x, point.co.y, point.co.z)),
                radius=cls._threshold
            )[0]    # get first nearest (should be one)
            # get normals from src object
            src_vertex = src_obj.data.vertices[nearest[1]]
            # vertex_normal = src_vertex.normal
            vertex_normal, face_normal = cls._vertex_normals(
                obj=src_obj,
                vertex=src_vertex
            )
            # from what normal get tilt
            normal = None
            if rotate_v_imposters == 'Vertex':
                normal = vertex_normal
            elif rotate_v_imposters == 'Face':
                normal = face_normal
            # set tilt by selected normal
            if normal:
                normal2d = Vector((normal.x, normal.y))
                tilt = 0.0
                if obj_name[:1] == 'v':
                    # vertical
                    tilt = Vector((0.0, 1.0, 0.0)).angle(normal)
                    # check by sign
                    tilt_sign = -1 if Vector((0.0, 1.0)).angle_signed(normal2d, None) > 0 else 1
                    # check by curve direction
                    direction_sign = -1 if spline.points[0].co.z > spline.points[1].co.z else 1
                # elif obj_name[:1] == 'h':
                #     # horizontal
                    tilt *= tilt_sign * direction_sign
                # apply tilt to rotate imposter
                for point in spline.points:
                    point.tilt = tilt

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

    @classmethod
    def _vertex_normals(cls, obj, vertex):
        # get normal for the vertex of the obj
        # vertex normal - directly form vertex
        vertex_normal = vertex.normal
        # vertex_normal.normalize()
        # face normal - first linked face to the vertex, get via bmesh
        bm = bmesh.new()
        bm.from_mesh(obj.data)
        bm.verts.ensure_lookup_table()
        bm.edges.ensure_lookup_table()
        bm.faces.ensure_lookup_table()
        face_normal = bm.verts[vertex.index].link_faces[0].normal
        bm.free()
        return vertex_normal, face_normal


# OPERATORS

class Vitragen_OT_generate_imposters(Operator):
    bl_idname = 'vitragen.generate_imposters'
    bl_label = 'Generate Imposters'
    bl_description = 'Generate Imposters'
    bl_options = {'REGISTER', 'UNDO'}

    width_hi = FloatProperty(
        name='Horizontal Inner Width',
        default=0.05,
        min=0.0
    )

    width_ho = FloatProperty(
        name='Horizontal Outer Width',
        default=0.08,
        min=0.0
    )

    width_vi = FloatProperty(
        name='Vertical Inner Width',
        default=0.05,
        min=0.0
    )

    width_vo = FloatProperty(
        name='Vertical Outer Width',
        default=0.08,
        min=0.0
    )

    rotate_v_imposters = EnumProperty(
        name='Normal align',
        items=[
            ('None', 'None', 'None', '', 0),
            ('Face', 'Face', 'Face', '', 1),
            ('Vertex', 'Vertex', 'Vertex', '', 2)
        ],
        default='Face',
        description='Defines alignment of a vertical imposts. On stands for the average, off stands for the nearest side'
    )
    reuse_bevel_objects = BoolProperty(
        name='Reuse bevel objects',
        default=True
    )

    def execute(self, context):
        Vitragen.generate_imposters(
            context=context,
            src_obj=context.active_object,
            hiw=self.width_hi,
            how=self.width_ho,
            viw=self.width_vi,
            vow=self.width_vo,
            rotate_v_imposters=self.rotate_v_imposters,
            reuse_bevel_objects=self.reuse_bevel_objects
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
        op.rotate_v_imposters = context.scene.vitragen_rotate_v_imposters
        op.reuse_bevel_objects = context.scene.vitragen_reuse_bevel_objects
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
        layout.prop(
            data=context.scene,
            property='vitragen_rotate_v_imposters',
            expand=True
        )
        layout.prop(
            data=context.scene,
            property='vitragen_reuse_bevel_objects'
        )


# REGISTER

def register():
    Scene.vitragen_width_hi = FloatProperty(
        name='Horizontal Inner Width',
        default=0.05,
        min=0.0
    )
    Scene.vitragen_width_ho = FloatProperty(
        name='Horizontal Outer Width',
        default=0.08,
        min=0.0
    )
    Scene.vitragen_width_vi = FloatProperty(
        name='Vertical Inner Width',
        default=0.05,
        min=0.0
    )
    Scene.vitragen_width_vo = FloatProperty(
        name='Vertical Outer Width',
        default=0.08,
        min=0.0
    )
    Scene.vitragen_rotate_v_imposters = EnumProperty(
        name='Normal align',
        items=[
            ('None', 'None', 'None', '', 0),
            ('Face', 'Face', 'Face', '', 1),
            ('Vertex', 'Vertex', 'Vertex', '', 2)
        ],
        default='Face',
        description='Defines alignment of a vertical imposts. On stands for the average, off stands for the nearest side'
    )
    Scene.vitragen_reuse_bevel_objects = BoolProperty(
        name='Reuse bevel objects',
        default=True
    )
    register_class(Vitragen_OT_generate_imposters)
    register_class(Vitragen_PT_panel)


def unregister():
    unregister_class(Vitragen_PT_panel)
    unregister_class(Vitragen_OT_generate_imposters)
    del Scene.vitragen_reuse_bevel_objects
    del Scene.vitragen_rotate_v_imposters
    del Scene.vitragen_width_hi
    del Scene.vitragen_width_ho
    del Scene.vitragen_width_vi
    del Scene.vitragen_width_vo


if __name__ == "__main__":
    register()
