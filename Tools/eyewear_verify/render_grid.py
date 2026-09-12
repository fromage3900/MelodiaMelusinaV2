"""Quick preview render of the silhouette grid."""
import bpy

bpy.context.scene.render.filepath = r"P:/MelodiaMelusinaV2-Laptop/Saved/Accessories/preview_grid_"
bpy.ops.render.render(write_still=True)
print("Rendered to", bpy.context.scene.render.filepath + ".png")
