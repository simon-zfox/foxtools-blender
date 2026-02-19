from . import helpers
from .properties import FoxToolsProperties
from bpy.props import StringProperty, IntProperty, EnumProperty, PointerProperty, BoolProperty
from bpy.types import Panel, Operator, PropertyGroup, UILayout
import bpy


class AutoBake(Operator):
    bl_idname = "object.production_bake"
    bl_label = "Bake Textures"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):

        props= context.scene.foxToolsProperties
        obj: bpy.types.Object | None = context.active_object

        if not obj or not obj.active_material:
            self.report({'ERROR'}, "No active object/material")
            return {'CANCELLED'}

        mat = obj.active_material

        if not mat.use_nodes or not mat.node_tree:
            self.report({'ERROR'}, "Material does not use nodes")
            return {'CANCELLED'}

        nodes = mat.node_tree.nodes
        links = mat.node_tree.links

        # Rename
        obj.name = props.base_name
        obj.data.name = props.base_name
        mat.name = props.base_name

        # Cycles Setup
        helpers.setup_cycles(context)

        # Cleanup
        helpers.cleanup_previous_bake(mat)

        # Source Principled
        principled_nodes = [n for n in nodes if n.type == 'BSDF_PRINCIPLED']
        if not principled_nodes:
            self.report({'ERROR'}, "No Principled BSDF found")
            return {'CANCELLED'}

        source_bsdf = principled_nodes[int(props.principled_choice)]

        # =====================================================
        # CREATE NODES
        # =====================================================

        # Images
        def create_image(suffix):
            return bpy.data.images.new(
                f"{props.base_name}_{suffix}",
                width=props.res_x,
                height=props.res_y,
                alpha=True
            )

        img_diff = create_image("d")
        img_norm = create_image("n")
        img_rough = create_image("r")

        tex_diff = nodes.new("ShaderNodeTexImage")
        tex_norm = nodes.new("ShaderNodeTexImage")
        tex_norm.color_space = 'Non-Color'
        tex_rough = nodes.new("ShaderNodeTexImage")

        tex_diff.image = img_diff
        tex_norm.image = img_norm
        tex_rough.image = img_rough

        normal_map = nodes.new("ShaderNodeNormalMap")

        new_bsdf = nodes.new("ShaderNodeBsdfPrincipled")

        # Werte kopieren
        for input_name in source_bsdf.inputs.keys():
            try:
                new_bsdf.inputs[input_name].default_value = source_bsdf.inputs[input_name].default_value
            except:
                pass

        mix_shader = nodes.new("ShaderNodeMixShader")
        mix_shader["is_bake_switch"] = True

        # =====================================================
        # AUTO-LAYOUT rechts vom gesamten Node-Tree
        # =====================================================

        output = next((n for n in nodes if n.type == 'OUTPUT_MATERIAL'), None)

        max_x = max(node.location.x for node in nodes)
        MARGIN_RIGHT = 600
        SPACING_X = 350
        SPACING_Y = 260

        start_x = max_x + MARGIN_RIGHT
        center_y = output.location.y if output else 0

        new_bsdf.location = (start_x, center_y)
        mix_shader.location = (start_x + SPACING_X, center_y)

        tex_diff.location = (start_x - SPACING_X * 2, center_y + SPACING_Y)
        tex_norm.location = (start_x - SPACING_X * 2, center_y)
        tex_rough.location = (start_x - SPACING_X * 2, center_y - SPACING_Y)

        normal_map.location = (start_x - SPACING_X, center_y)

        # =====================================================
        # LINKING
        # =====================================================

        links.new(tex_norm.outputs["Color"], normal_map.inputs["Color"])
        links.new(normal_map.outputs["Normal"], new_bsdf.inputs["Normal"])

        links.new(tex_diff.outputs["Color"], new_bsdf.inputs["Base Color"])
        links.new(tex_diff.outputs["Alpha"], new_bsdf.inputs["Alpha"])
        links.new(tex_rough.outputs["Color"], new_bsdf.inputs["Roughness"])

        if output:
            links.new(source_bsdf.outputs["BSDF"], mix_shader.inputs[1])
            links.new(new_bsdf.outputs["BSDF"], mix_shader.inputs[2])
            links.new(mix_shader.outputs["Shader"], output.inputs["Surface"])

        mix_shader.inputs[0].default_value = 0.0

        # =====================================================
        # FRAME
        # =====================================================

        frame = nodes.new("NodeFrame")
        frame.label = "BAKE_BLOCK"
        frame.use_custom_color = True
        frame.color = (0.1, 0.6, 0.2)

        for n in [tex_diff, tex_norm, tex_rough, normal_map, new_bsdf, mix_shader]:
            n.parent = frame

        # =====================================================
        # BAKE
        # =====================================================

        wm = context.window_manager
        if wm is None:
            self.report({'ERROR'}, "No window manager found")
            return {'CANCELLED'}
        wm.progress_begin(0, 3)

        scene = context.scene
        bake_settings = scene.render.bake

        def bake(tex_node, bake_type):
            nodes.active = tex_node
            bpy.context.view_layer.objects.active = obj
            obj.select_set(True)
            bpy.ops.object.bake(type=bake_type)

        # Diffuse
        bake_settings.use_pass_direct = False
        bake_settings.use_pass_indirect = False
        bake_settings.use_pass_color = True

        bake(tex_diff, 'DIFFUSE')
        wm.progress_update(1)

        # Normal
        bake(tex_norm, 'NORMAL')
        wm.progress_update(2)

        # Roughness
        bake(tex_rough, 'ROUGHNESS')
        wm.progress_update(3)

        wm.progress_end()

        # Pack Images
        img_diff.pack()
        img_norm.pack()
        img_rough.pack()

        mix_shader.inputs[0].default_value = 1.0

        self.report({'INFO'}, "Bake finished")
        return {'FINISHED'}


# =========================================================
# Global Toggle
# =========================================================


# =========================================================
# UI Panel
# =========================================================
