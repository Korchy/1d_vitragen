# Nikita Akimov
# interplanety@interplanety.org
#
# GitHub
#    https://github.com/Korchy/1d_vitragen

from bpy.props import FloatProperty
from bpy.types import Operator, Panel, Scene
from bpy.utils import register_class, unregister_class

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

    @classmethod
    def generate_imposters(cls, context, src_obj, hiw=1.0, how=1.0, viw=1.0, vow=1.0):
        # generate frames (imposters) for src_obj 
        pass


# OPERATORS

class Vitragen_OT_generate_imposters(Operator):
    bl_idname = 'vitragen.generate_imposters'
    bl_label = 'Generate Imposters'
    bl_description = 'Generate Imposters'
    bl_options = {'REGISTER', 'UNDO'}

    width_hi = FloatProperty(
        name='Horizontal Inner Width',
        default=1.0
    )

    width_ho = FloatProperty(
        name='Horizontal Outer Width',
        default=1.0
    )

    width_vi = FloatProperty(
        name='Vertical Inner Width',
        default=1.0
    )

    width_vo = FloatProperty(
        name='Vertical Outer Width',
        default=1.0
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
        default=1.0
    )
    Scene.vitragen_width_ho = FloatProperty(
        name='Horizontal Outer Width',
        default=1.0
    )
    Scene.vitragen_width_vi = FloatProperty(
        name='Vertical Inner Width',
        default=1.0
    )
    Scene.vitragen_width_vo = FloatProperty(
        name='Vertical Outer Width',
        default=1.0
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
