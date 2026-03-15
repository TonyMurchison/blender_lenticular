import bpy
from bpy_extras.io_utils import ImportHelper
import os.path
import math
import bmesh


class lent_load_main(bpy.types.Operator, ImportHelper):
    # Load primary images for lenticular generation
    bl_idname = "lent.load_primary"
    bl_label = "Load images"
    bl_options = {"REGISTER", "UNDO"}

    directory: bpy.props.StringProperty(subtype="DIR_PATH")
    files: bpy.props.CollectionProperty(name="File Path", type=bpy.types.OperatorFileListElement)

    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)

        return {"RUNNING_MODAL"}

    def execute(self, context):
        # Check for multiple image files
        try:
            self.files[1]
        except:
            self.report({"WARNING"}, "Not enough files selected.")
            return {"CANCELLED"}

        try:
            bpy.ops.image.import_as_mesh_planes(
                directory=self.directory,
                files=[{"name": self.files[0].name}]
            )
        except:
            self.report(
                {"ERROR"}, "Image loading failed.")
            return {"CANCELLED"}

        obj = bpy.data.objects[os.path.splitext(self.files[0].name)[0]]
        obj.name = "Lenticular Print"

        # Make file paths accessible to create_material
        scene = context.scene
        scene.import_dir = self.directory
        scene.import_f.clear()
        for f in self.files:
            item = scene.import_f.add()
            item.name = f.name

        return {"FINISHED"}

class lent_create_material(bpy.types.Operator):
    # Create dynamic material that blends input images at present band width
    bl_idname = "lent.create_material"
    bl_label = "Update banding pattern"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        obj = bpy.context.active_object

        scene = context.scene
        img1_path = os.path.join(scene.import_dir, scene.import_f[0].name)
        img2_path = os.path.join(scene.import_dir, scene.import_f[1].name)

        mat = bpy.data.materials.new("LentImageMaterial")
        mat.use_nodes = True

        nodes = mat.node_tree.nodes
        links = mat.node_tree.links

        nodes.clear()

        output = nodes.new("ShaderNodeOutputMaterial")
        output.location = (600, 0)

        bsdf = nodes.new("ShaderNodeBsdfPrincipled")
        bsdf.inputs["Emission Strength"].default_value = 3
        bsdf.location = (350, 0)

        mix = nodes.new("ShaderNodeMix")
        mix.data_type = 'RGBA'
        mix.location = (150, 0)

        wave = nodes.new("ShaderNodeTexWave")
        wave.location = (-400, 150)
        wave.wave_type = 'BANDS'
        wave.bands_direction = 'X'

        coord = nodes.new("ShaderNodeTexCoord")
        coord.location = (-650, 100)

        # Here because you can't directly access wave.scale
        scale = nodes.new("ShaderNodeValue")
        scale.location = (-650, 200)
        # Empirical conversion factor between scale -> band width for world UVs
        scaleval = 1 / bpy.context.scene.band_width
        scale.outputs[0].default_value = scaleval * 156.06

        round_node = nodes.new("ShaderNodeMath")
        round_node.operation = 'ROUND'
        round_node.location = (-150, 150)

        img1 = nodes.new("ShaderNodeTexImage")
        img1.location = (-400, -50)
        img1.image = bpy.data.images.load(img1_path)

        img2 = nodes.new("ShaderNodeTexImage")
        img2.location = (-400, -200)
        img2.image = bpy.data.images.load(img2_path)

        # Draw links between components.
        links.new(wave.outputs["Color"], round_node.inputs[0])
        links.new(scale.outputs[0], wave.inputs["Scale"])
        links.new(round_node.outputs["Value"], mix.inputs["Factor"])
        links.new(coord.outputs["Object"], wave.inputs["Vector"])
        links.new(img1.outputs["Color"], mix.inputs["A"])
        links.new(img2.outputs["Color"], mix.inputs["B"])
        links.new(mix.outputs["Result"], bsdf.inputs["Base Color"])
        links.new(bsdf.outputs["BSDF"], output.inputs["Surface"])
        # EEVEE refraction materials are a little annoying, so illuminating from below helps
        links.new(mix.outputs["Result"], bsdf.inputs["Emission Color"])

        if obj.data.materials:
            obj.data.materials[0] = mat
        else:
            obj.data.materials.append(mat)
        return {"FINISHED"}


class lent_create_lens(bpy.types.Operator):
    # Whole lens creation process, from curve drawing to materials.
    bl_idname = "lent.create_lens"
    bl_label = "Create lens"
    bl_options = {"REGISTER", "UNDO"}

    def find_edge(self, obj):
        # Find and build the horizontal lower edge of the image plane
        v = obj.data.vertices
        verts = [(v.co.x, v.co.y, v.co.z) for v in obj.data.vertices]
        lowverts = sorted(verts, key=lambda v: v[1])[:2]
        low_sorted = sorted(lowverts, key=lambda v: v[0])
        mesh = bpy.data.meshes.new("Lens")
        meshobj = bpy.data.objects.new("Lens", mesh)
        bpy.context.collection.objects.link(meshobj)

        mesh.from_pydata(low_sorted, [(0,1)], [])

        return meshobj

    def build_lens_segment(self, edge, pointcount):
        # Using the lower edge as a starting point, build an arc segment at the corner.
        v = edge.data.vertices[0]
        vc = (v.co.x, v.co.y, v.co.z)

        segment_v = []

        # Get factors and convert to mm
        wm, rm, hm = bpy.context.scene.band_width, bpy.context.scene.lens_radius, bpy.context.scene.lens_thickness
        w, r, h = wm/500, rm/1000, hm/1000

        alpha = math.asin(w / (2*r)) # Angle for a half lens units
        offset = (0.5 * w, h - r)
        # Create half-arc, not counting the top of the arc
        # There's probably a built-in function for this, but I didn't learn trigonometry for nothing
        for i in range(1, int((pointcount/2))):
            angle = alpha / (pointcount/2) * i
            xc = r * math.sin(angle) + offset[0] + vc[0]
            zc = r * math.cos(angle) + offset[1] + vc[2]
            segment_v.append((xc, v.co.y, zc))

        # Mirror the arc segment and generate a midpoint
        arc = []
        # Always in the X direction, so we can just subtract the X-coord difference
        for v in reversed(segment_v):
            mirror_point_x = vc[0] + offset[0]
            x_mirrored = v[0] - (2*(v[0]-mirror_point_x))
            v_mirrored = (x_mirrored, v[1], v[2])
            arc.append(v_mirrored)

        midpoint = (vc[0] + offset [0], vc[1], vc[2] + h)
        arc.append(midpoint)
        arc = arc + segment_v
        print(str(arc))

        # convert the point list into a mesh
        mesh = bpy.data.meshes.new("Arc")
        meshobj = bpy.data.objects.new("Arc", mesh)
        bpy.context.collection.objects.link(meshobj)

        # Compile vertex joints
        segment_e = []
        for i in range((len(arc) - 1)):
            segment_e.append((i, i+1))
        mesh.from_pydata(arc, segment_e, [])
        mesh.update()

        return meshobj

    def array_lens(self, lens_segment, edge_mesh):
        # Create a curve representing the cross-section of the whole lenticular lens

        # Populate edge with copies of the lens segment
        edge_length = edge_mesh.data.vertices[1].co.x - edge_mesh.data.vertices[0].co.x
        lens_width = lens_segment.data.vertices[-1].co.x - lens_segment.data.vertices[0].co.x

        lens_array = lens_segment.modifiers.new(name="LensArray", type= 'ARRAY')

        lens_array.count = int(edge_length // lens_width)
        lens_array.relative_offset_displace = (1, 0, 0)
        lens_array.use_relative_offset = True
        lens_array.use_merge_vertices = True
        lens_array.merge_threshold = 0.001

        # Apply modifier, since we'll need access to all vertices
        bpy.context.view_layer.objects.active = lens_segment
        bpy.ops.object.modifier_apply(modifier=lens_array.name)

        # Extend the curve sequence to Z 0
        v_start = lens_segment.data.vertices[0].co
        v_end = lens_segment.data.vertices[-1].co
        lens_segment.data.vertices.add(2)
        lens_segment.data.vertices[-2].co = (v_start[0], v_start[1], 0)
        lens_segment.data.vertices[-1].co = (v_end[0], v_start[1], 0)

        lens_segment.data.edges.add(3)
        vcount = len(lens_segment.data.vertices)
        lens_segment.data.edges[-3].vertices = (0, vcount - 2)
        lens_segment.data.edges[-2].vertices = (vcount - 1, vcount - 3)

        # Close off the loop
        lens_segment.data.edges[-1].vertices = (vcount - 1, vcount - 2)

        return lens_segment

    def make_lens(self, lens_outline):
        # Extrude outline

        # Make into face.
        bpy.ops.object.select_all(action= 'DESELECT')
        lens_outline.select_set(True)
        bpy.context.view_layer.objects.active = lens_outline
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.edge_face_add()
        ex_vec = (0, 1, 0) #default import height for any given image
        bpy.ops.mesh.extrude_region()
        bpy.ops.transform.translate(value=ex_vec)
        bpy.ops.object.mode_set(mode='OBJECT')

        return lens_outline

    def lens_material(self, lens):
        if "LensMaterial" in bpy.data.materials:
            mat = bpy.data.materials["LensMaterial"]
        else:
            mat = bpy.data.materials.new("LensMaterial")

        mat.use_nodes = True
        nodes = mat.node_tree.nodes
        links = mat.node_tree.links

        for n in nodes:
            nodes.remove(n)

        ref = nodes.new(type="ShaderNodeBsdfRefraction")
        ref.location = (0, 0)
        ref.inputs["Roughness"].default_value = 0.0
        ref.inputs["IOR"].default_value = bpy.context.scene.ior

        output = nodes.new(type="ShaderNodeOutputMaterial")
        output.location = (300, 0)

        links.new(ref.outputs["BSDF"], output.inputs["Surface"])

        # Enable Eevee refraction
        mat.use_screen_refraction = True
        mat.blend_method = 'BLEND'
        mat.refraction_depth = 0.005
        bpy.context.scene.eevee.use_raytracing = True

        # Assign material
        lens.data.materials.append(mat)
        bpy.context.object.active_material.surface_render_method = 'DITHERED'

    def execute(self, context):
        edge = self.find_edge(bpy.context.active_object)
        lens_segment = self.build_lens_segment(edge, pointcount=11) # Maybe make higher for larger band widths
        lens_outline = self.array_lens(lens_segment, edge)
        lens = self.make_lens(lens_outline)
        self.lens_material(lens)

        # File clean-up
        bpy.data.objects.remove(edge, do_unlink=True)
        obj = bpy.data.objects["Arc"]
        obj.name = "Lens"
        return {"FINISHED"}

class lent_main_panel(bpy.types.Panel):
    # Sidebar panel
    bl_label = "Lenticular"
    bl_idname = "main_panel"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Lenticular"   # Tab label in the sidebar

    def draw(self, context):
        layout = self.layout

        layout.label(text="Combine images into a lenticular print")
        layout.separator()
        layout.operator("lent.load_primary", icon="MESH_PLANE")
        layout.separator()
        layout.prop(context.scene, "band_width")
        layout.operator("lent.create_material", icon="IMAGE_BACKGROUND")
        layout.separator()
        layout.prop(context.scene, "lens_radius")
        layout.prop(context.scene, "lens_thickness")
        layout.prop(context.scene, "ior")
        layout.separator()
        layout.operator("lent.create_lens", icon="MESH_CIRCLE")

