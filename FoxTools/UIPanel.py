import bpy
from bpy.types import Operator, Panel

from .FTProps import FTProps


class VIEW3D_PT_NPanel(Panel):
    bl_label = "Auto Bake"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "FoxTools"

    def draw(self, context):
        layout = self.layout
        if layout is None:
            return
        props = FTProps.getprop(context)

        layout.prop(props, "base_name")
        layout.prop(props, "res_x")
        layout.prop(props, "res_y")
        layout.prop(props, "principled_choice")

        layout.separator()
        layout.operator("object.foxtools_autobake")
        layout.operator("object.foxtools_autobake_cleanup")

        layout.separator()
        layout.label(text="Toggle View: (currently rendering " + ("Baked" if props.baked_view else "Original") + ")")
        layout.operator("object.toggle_bake_view")


class UIToggleBakeView(Operator):
    bl_idname = "object.toggle_bake_view"
    bl_label = "Toggle all Materials"
    bl_description = "Toggle between baked and original view for all materials that have been processed by AutoBake."
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):

        props = FTProps.getprop(context)
        props.baked_view = not props.baked_view

        for mat in bpy.data.materials:
            if not mat.use_nodes:
                continue
            for node in mat.node_tree.nodes:
                if "ft_autobake_switch" in node:
                    node.inputs[0].default_value = "Baked" if props.baked_view else "Original"

        return {'FINISHED'}
