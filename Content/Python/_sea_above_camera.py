import unreal
import json

# Set viewport camera to focus on cathedral
# Cathedral center: (0, 0, 13405)

# Get the viewport client
viewport_client = unreal.get_default_object(unreal.EditorViewportClient)
if viewport_client:
    # Set camera location and rotation
    cam_loc = unreal.Vector(0, -5000, 15000)  # Looking at cathedral from front
    cam_rot = unreal.Rotator(-10, 0, 0)  # Slight downward tilt
    viewport_client.set_view_location(cam_loc)
    viewport_client.set_view_rotation(cam_rot)
    viewport_client.set_ortho(False)
    print(f"Camera set to: {cam_loc}")
else:
    print("No viewport client")

# Alternative: use console command
unreal.SystemLibrary.execute_console_command(unreal.EditorLevelLibrary.get_editor_world(), "Camera 0 -5000 15000")
print("Camera command executed")
