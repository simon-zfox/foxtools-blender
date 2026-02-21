from . import helpers
from .FTProps import FTProps
from bpy.types import Node, Operator, ShaderNodeTexImage
import bpy


class AutoBakeCleanup(Operator):
    bl_idname = "object.foxtools_autobake_cleanup"
    bl_label = "Cleanup AutoBake Nodes"
    bl_description = "Cleanup all nodes created by the AutoBake operator on the selected object."
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        images_to_remove = []
        nodes_to_remove = []
        obj = context.active_object

        if not obj or not obj.active_material or not obj.active_material.use_nodes or not obj.active_material.node_tree or not obj.active_material.node_tree.nodes:
            self.report({'ERROR'}, "Active object must have a material with a node tree.")
            return {'CANCELLED'}

        nodes = obj.active_material.node_tree.nodes
        links = obj.active_material.node_tree.links

        # collect nodes to remove
        for node in list(nodes):
            if "ft_autobake" in node:
                if isinstance(node, ShaderNodeTexImage) and node.image:
                    images_to_remove.append(node.image)
                nodes_to_remove.append(node)

        # find nodes to reconnect
        output = next((n for n in nodes if n.type == 'OUTPUT_MATERIAL'), None)
        before_output: Node | None = None
        for node in nodes:
            if "ft_autobake_before_output" in node:
                before_output = node
                break

        if output is None or before_output is None:
            self.report({'ERROR'}, "No nodes found that were created by AutoBake.")
            return {'CANCELLED'}

        # reconnect nodes
        links.new(before_output.outputs[0], output.inputs[0])
        for node in nodes_to_remove:
            nodes.remove(node)
        for img in images_to_remove:
            if img.users == 0:
                bpy.data.images.remove(img)

        # reposition output node
        output.location.x = before_output.location.x + 300
        output.location.y = before_output.location.y

        self.report({'INFO'}, f"AutoBake nodes cleaned up. Removed {len(nodes_to_remove)} nodes and {len(images_to_remove)} images.")
        return {'FINISHED'}
