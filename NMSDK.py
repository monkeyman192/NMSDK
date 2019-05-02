from bpy.props import StringProperty, BoolProperty  # noqa pylint: disable=import-error, no-name-in-module

# ExportHelper is a helper class, defines filename and
# invoke() function which calls the file selector.
from bpy_extras.io_utils import ExportHelper, ImportHelper  # noqa pylint: disable=import-error
from bpy.types import Operator  # noqa pylint: disable=import-error, no-name-in-module

from .ModelImporter.import_scene import ImportScene
from .ModelExporter.addon_script import Exporter


# operators to be used for the public API


class ImportSceneOperator(Operator):
    """ Import an entire scene into the current blender context."""
    bl_idname = "nmsdk.import_scene"
    bl_label = "Import NMS Scene file"

    path = StringProperty(default="")

    def execute(self, context):
        importer = ImportScene(self.path, parent_obj=None, ref_scenes=dict())
        importer.render_scene()
        return importer.state


class ImportMeshOperator(Operator):
    """ Import one or more individual meshes from a single scene into the
    current blender context. """
    bl_idname = "nmsdk.import_mesh"
    bl_label = "Import NMS meshes"

    path = StringProperty(default="")
    mesh_id = StringProperty(default="")

    def execute(self, context):
        importer = ImportScene(self.path, parent_obj=None, ref_scenes=dict())
        importer.render_mesh(str(self.mesh_id))
        return importer.state


# operators to be added to the blender UI for various tasks


class NMS_Export_Operator(Operator, ExportHelper):
    """Export scene to NMS compatible files"""
    # important since its how bpy.ops.import_test.some_data is constructed
    bl_idname = "export_mesh.nms"
    bl_label = "Export to NMS XML Format"

    # ExportHelper mixin class uses this
    filename_ext = ""

    def execute(self, context):
        main_exporter = Exporter(self.filepath)
        status = main_exporter.state
        self.report({'INFO'}, "Models Exported Successfully")
        if status:
            return {'FINISHED'}
        else:
            return {'CANCELLED'}


class NMS_Import_Operator(Operator, ImportHelper):
    """Import NMS Scene files."""
    # important since its how bpy.ops.import_test.some_data is constructed
    bl_idname = "import_mesh.nms"
    bl_label = "Import from SCENE.EXML"

    # ExportHelper mixin class uses this
    filename_ext = ".EXML"

    clear_scene = BoolProperty(
        name='Clear scene',
        description='Whether or not to clear the currently exiting scene in '
                    'blender.',
        default=True)

    draw_hulls = BoolProperty(
        name='Draw bounded hulls',
        description='Whether or not to draw the points that make up the '
                    'bounded hulls of the materials. This is only for research'
                    '/debugging, so can safely be left as False.',
        default=False)

    def draw(self, context):
        layout = self.layout
        layout.prop(self, 'draw_hulls')
        layout.prop(self, 'clear_scene')

    def execute(self, context):
        keywords = self.as_keywords()
        fdir = self.properties.filepath
        print(fdir)
        importer = ImportScene(fdir, parent_obj=None, ref_scenes=dict(),
                               settings=keywords)
        importer.render_scene()
        status = importer.state
        self.report({'INFO'}, "Models Imported Successfully")
        print('Scene imported!')
        if status:
            return {'FINISHED'}
        else:
            return {'CANCELLED'}
