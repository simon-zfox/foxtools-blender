import bpy
from bpy.types import Operator, Panel

from .properties import FoxToolsProperties


class NPanel(Panel):
    bl_label = "Production Bake Tool"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "BakeTool"

    def draw(self, context):
        layout = self.layout
        if layout is None:
            return
        props = context.scene.foxToolsProperties

        layout.prop(props, "base_name")
        layout.prop(props, "res_x")
        layout.prop(props, "res_y")
        layout.prop(props, "principled_choice")

        layout.separator()
        layout.operator("object.production_bake")

        layout.separator()
        layout.operator("object.toggle_bake_view")


class UIToggleBakeView(Operator):
    bl_idname = "object.toggle_bake_view"
    bl_label = "Toggle All Materials"

    def execute(self, context):

        props = context.scene.foxToolsProperties
        props.baked_view = not props.baked_view

        for mat in bpy.data.materials:
            if not mat.use_nodes:
                continue
            for node in mat.node_tree.nodes:
                if node.type == "MIX_SHADER" and "is_bake_switch" in node:
                    node.inputs[0].default_value = 1.0 if props.baked_view else 0.0

        return {'FINISHED'}
