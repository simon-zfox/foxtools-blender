from . import helpers
from .FTProps import FTProps
from bpy.types import Operator, ShaderNodeTexImage
import bpy


class AutoBake(Operator):
    bl_idname = "object.foxtools_autobake"
    bl_label = "Automatic bake Textures"
    bl_description = "Automatically bake Diffuse, Normal and Roughness maps from the selected Principled BSDF shader.\n" \
                     "Intended to be used with materials created by MekTools, an FFXIV model import tool.\n\n" \
                     "Usually the first (default) Principled BSDF shader is the correct one"
    bl_options = {'REGISTER', 'UNDO'}

    # varous attributs of blender file
    context: bpy.types.Context
    obj: bpy.types.Object
    material: bpy.types.Material
    nodes: bpy.types.NodeTree
    node_links: bpy.types.NodeLinks
    props: FTProps
    source_bsdf: bpy.types.ShaderNodeBsdfPrincipled
    wm: bpy.types.WindowManager
    scene: bpy.types.Scene

    # newly created nodes
    img_diff: bpy.types.Image
    img_norm: bpy.types.Image
    img_rough: bpy.types.Image
    node_tex_diff: ShaderNodeTexImage
    node_tex_norm: ShaderNodeTexImage
    node_tex_rough: ShaderNodeTexImage
    node_normal_map: bpy.types.ShaderNodeNormalMap
    node_new_bsdf: bpy.types.ShaderNodeBsdfPrincipled
    node_switch: bpy.types.GeometryNodeMenuSwitch

    def init_class_vars(self, context: bpy.types.Context):
        self.props = FTProps.getprop(context)
        self.context = context

        if not self.context.active_object or not self.context.active_object.active_material:
            self.report({'ERROR'}, "Error accessing active object")
            return False
        self.obj = self.context.active_object

        if not self.context.active_object.active_material:
            self.report({'ERROR'}, "Error accessing active material")
            return False
        self.material = self.context.active_object.active_material

        if not self.context.active_object.active_material.use_nodes or not self.context.active_object.active_material.node_tree:
            self.report({'ERROR'}, "Material does not use nodes")
            return False

        if not self.context.active_object.active_material.node_tree:
            self.report({'ERROR'}, "Material has no nodes")
            return False
        self.nodes = self.context.active_object.active_material.node_tree.nodes

        if not self.context.active_object.active_material.node_tree.links:
            self.report({'ERROR'}, "Material has no node links")
            return False
        self.node_links = self.context.active_object.active_material.node_tree.links

        source_bsdf_list = helpers.get_principled_nodes(self.context)
        source_bsdf = source_bsdf_list[int(self.props.principled_choice)] if source_bsdf_list else None
        if not source_bsdf:
            self.report({'ERROR'}, "Could not find source Principled BSDF")
            return False
        self.source_bsdf = source_bsdf

        if not self.context.window_manager:
            self.report({'ERROR'}, "No window manager found")
            return False
        self.wm = self.context.window_manager

        if not self.context.scene:
            self.report({'ERROR'}, "No scene found")
            return False
        self.scene = self.context.scene

        return True

    def create_image(self, suffix) -> bpy.types.Image:
        return bpy.data.images.new(
            f"{self.props.base_name}_{suffix}",
            width=self.props.res_x,
            height=self.props.res_y,
            alpha=True
        )

    def create_node(self, node_type: str):
        node = self.nodes.new(node_type)  # pyright: ignore[reportAttributeAccessIssue]
        node["ft_autobake"] = True  # Mark node as created by this addon for easier cleanup later
        if not node:
            self.report({'ERROR'}, f"Error creating node of type {node_type}")
            raise Exception(f"Error creating node of type {node_type}")
        return node

    def create_init_nodes(self):
        self.img_diff = self.create_image("d")
        self.img_norm = self.create_image("n")
        self.img_rough = self.create_image("r")

        self.node_tex_diff = self.create_node("ShaderNodeTexImage")
        self.node_tex_norm = self.create_node("ShaderNodeTexImage")
        self.node_tex_rough = self.create_node("ShaderNodeTexImage")

        # Set color space to Non-Color for normal and roughness maps
        if not self.img_norm.colorspace_settings or not self.img_rough.colorspace_settings:
            self.report({'ERROR'}, "Error accessing image color space settings")
            return False
        self.img_norm.colorspace_settings.name = 'Non-Color'
        self.img_rough.colorspace_settings.name = 'Non-Color'

        self.node_tex_diff.image = self.img_diff
        self.node_tex_norm.image = self.img_norm
        self.node_tex_rough.image = self.img_rough

        self.node_normal_map = self.create_node("ShaderNodeNormalMap")
        self.node_new_bsdf = self.create_node("ShaderNodeBsdfPrincipled")

        # Copy values from source BSDF to new BSDF
        for input_name in self.source_bsdf.inputs.keys():
            try:
                self.node_new_bsdf.inputs[input_name].default_value = self.source_bsdf.inputs[input_name].default_value
            except:
                pass

        self.node_switch = self.create_node("GeometryNodeMenuSwitch")
        self.node_switch.data_type = 'SHADER'
        self.node_switch["ft_autobake_switch"] = True
        self.node_switch.enum_items.clear()
        self.node_switch.enum_items.new("Original")
        self.node_switch.enum_items.new("Baked")

        return True

    def link_layout_nodes(self):
        output = next((n for n in self.nodes if n.type == 'OUTPUT_MATERIAL'), None)
        if not output:
            self.report({'ERROR'}, "No Material Output node found")
            return False

        before_output_node = next((link.from_node for link in self.node_links if link.to_node ==
                                  output and link.to_socket.name == "Surface"), None)
        if not before_output_node:
            self.report({'ERROR'}, "No node connected to Material Output found")
            return False
        before_output_node["ft_autobake_before_output"] = True

        max_x = max(node.location.x for node in self.nodes)
        MARGIN_RIGHT = 800
        SPACING_X = 350
        SPACING_Y = 350

        start_x = max_x + MARGIN_RIGHT
        start_y = output.location.y + SPACING_Y

        self.node_new_bsdf.location = (start_x, start_y + SPACING_Y)
        self.node_switch.location = (start_x + SPACING_X, start_y + SPACING_Y)
        output.location = (start_x + SPACING_X * 2, start_y + SPACING_Y)

        self.node_tex_diff.location = (start_x - SPACING_X * 2, start_y + 2 * SPACING_Y)
        self.node_tex_norm.location = (start_x - SPACING_X * 2, start_y + SPACING_Y)
        self.node_tex_rough.location = (start_x - SPACING_X * 2, start_y)

        self.node_normal_map.location = (start_x - SPACING_X, start_y + SPACING_Y)

        # Linking

        self.node_links.new(self.node_tex_norm.outputs["Color"], self.node_normal_map.inputs["Color"])
        self.node_links.new(self.node_normal_map.outputs["Normal"], self.node_new_bsdf.inputs["Normal"])

        self.node_links.new(self.node_tex_diff.outputs["Color"], self.node_new_bsdf.inputs["Base Color"])
        self.node_links.new(self.node_tex_diff.outputs["Alpha"], self.node_new_bsdf.inputs["Alpha"])
        self.node_links.new(self.node_tex_rough.outputs["Color"], self.node_new_bsdf.inputs["Roughness"])

        self.node_links.new(before_output_node.outputs[0], self.node_switch.inputs["Original"])
        self.node_links.new(self.node_new_bsdf.outputs["BSDF"], self.node_switch.inputs["Baked"])
        self.node_links.new(self.node_switch.outputs["Output"], output.inputs["Surface"])

        self.node_switch.inputs["Menu"].default_value = "Original"

        # Frame

        frame = self.create_node("NodeFrame")
        frame.label = "FoxTools AutoBake"
        frame.use_custom_color = True
        frame.color = (0.1, 0.6, 0.2)

        for n in [self.node_tex_diff, self.node_tex_norm, self.node_tex_rough, self.node_normal_map, self.node_new_bsdf, self.node_switch, output]:
            n.parent = frame

        return True

    def bake_single(self, tex_node, bake_type):
        self.nodes.active = tex_node  # pyright: ignore[reportAttributeAccessIssue]
        bpy.context.view_layer.objects.active = self.obj  # pyright: ignore[reportOptionalMemberAccess]
        self.obj.select_set(True)
        bpy.ops.object.bake("EXEC_DEFAULT", type=bake_type)

    def bake(self):
        if not self.scene.render:
            self.report({'ERROR'}, "No render settings found")
            return False
        bake_settings = self.scene.render.bake
        if not bake_settings:
            self.report({'ERROR'}, "No bake settings found")
            return False

        # setup
        self.wm.progress_begin(0, 3)
        bake_settings.use_pass_direct = False
        bake_settings.use_pass_indirect = False
        bake_settings.use_pass_color = True

        self.bake_single(self.node_tex_diff, 'DIFFUSE')
        self.wm.progress_update(1)

        self.bake_single(self.node_tex_norm, 'NORMAL')
        self.wm.progress_update(2)

        self.bake_single(self.node_tex_rough, 'ROUGHNESS')
        self.wm.progress_update(3)

        self.wm.progress_end()

        return True

    def execute(self, context):
        success = self.init_class_vars(context)
        if not success:
            return {'CANCELLED'}

        helpers.setup_cycles(self.context)

        # Cleanup previous bake nodes if they exist to avoid clutter and potential issues with multiple bakes on the same material
        bpy.ops.object.foxtools_autobake_cleanup()  # pyright: ignore[reportAttributeAccessIssue]

        # Rename Mesh/Material
        self.obj.name = self.props.base_name
        self.obj.data.name = self.props.base_name  # pyright: ignore[reportOptionalMemberAccess]
        self.material.name = self.props.base_name

        success = self.create_init_nodes()
        if not success:
            return {'FINISHED'}

        success = self.link_layout_nodes()
        if not success:
            return {'FINISHED'}

        success = self.bake()
        if not success:
            return {'FINISHED'}

        # Pack Images
        self.img_diff.pack()
        self.img_norm.pack()
        self.img_rough.pack()

        # Set switch note show according to current view mode
        self.node_switch.inputs[0].default_value = "Baked" if self.props.baked_view else "Original"

        self.report({'INFO'}, "Bake finished")

        return {'FINISHED'}
