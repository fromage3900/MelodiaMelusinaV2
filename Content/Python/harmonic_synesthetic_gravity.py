"""
Harmonic Synesthetic Gravity (4D Audio-Architecture Folding) Controller
Bridges TouchDesigner Audio FFT Stream -> 4D Matrix Transforms -> UE Escher Geometry & MPC Parameters
"""

import socket, json, math, threading, time
import unreal

class HarmonicSynestheticGravityController:
    def __init__(self, host="127.0.0.1", port=55557):
        self.host = host
        self.port = port
        self.running = False
        self.sock = None
        self.thread = None

        # 4D Rotation angles
        self.theta_xy = 0.0
        self.theta_zw = 0.0
        self.bass_pulse = 0.0
        self.ripple_freq = 1.0

        self.mpc_path = "/Game/EnvSandbox/Materials/MPC_HarmonicGravity"

    def start_listening(self):
        self.running = True
        self.thread = threading.Thread(target=self._udp_loop, daemon=True)
        self.thread.start()
        print(f"[HarmonicGravity] Listening for TD 4D Audio Stream on {self.host}:{self.port}")

    def _udp_loop(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.bind((self.host, self.port))
        self.sock.settimeout(0.5)

        while self.running:
            try:
                data, addr = self.sock.recvfrom(2048)
                payload = json.loads(data.decode('utf-8'))
                self._process_payload(payload)
            except socket.timeout:
                continue
            except Exception as e:
                pass

    def _process_payload(self, data):
        sub_bass = data.get("bass", 0.0)
        mid_freq = data.get("mid", 0.0)
        high_freq = data.get("high", 0.0)

        # Calculate 4D angles
        self.theta_xy += mid_freq * 0.05
        self.theta_zw += high_freq * 0.03
        self.bass_pulse = sub_bass
        self.ripple_freq = 1.0 + high_freq * 10.0

        # Apply 4D Matrix to Escher Actors in Scene
        self._update_escher_4d_transforms()
        self._update_mpc_parameters()

    def _update_escher_4d_transforms(self):
        actors = unreal.GameplayStatics.get_all_actors_with_tag(unreal.EditorLevelLibrary.get_editor_world(), "EscherGeometry")

        # Compute 4D Rotor Matrix (R_4D)
        cos_xy, sin_xy = math.cos(self.theta_xy), math.sin(self.theta_xy)
        cos_zw, sin_zw = math.cos(self.theta_zw), math.sin(self.theta_zw)

        for actor in actors:
            loc = actor.get_actor_location()
            x, y, z = loc.x, loc.y, loc.z
            w = self.bass_pulse * 100.0  # 4th spatial dimension coordinate

            # 4D Rotation in (X,Y) and (Z,W) planes
            x_prime = x * cos_xy - y * sin_xy
            y_prime = x * sin_xy + y * cos_xy
            z_prime = z * cos_zw - w * sin_zw

            # 4D Perspective projection down to 3D space
            distance_4d = 1000.0
            scale_proj = distance_4d / (distance_4d + (w * 0.5))

            new_x = x_prime * scale_proj
            new_y = y_prime * scale_proj
            new_z = z_prime * scale_proj + (self.bass_pulse * 50.0) # Height extrusion on bass pulse

            actor.set_actor_location(unreal.Vector(new_x, new_y, new_z), False, False)
            actor.set_actor_rotation(unreal.Rotator(self.theta_zw * 57.29, self.theta_xy * 57.29, 0), False)

    def _update_mpc_parameters(self):
        mpc = unreal.load_asset(self.mpc_path)
        if mpc:
            unreal.MaterialEditingLibrary.set_material_parameter_collection_scalar_variable(
                mpc, "BassPulseIntensity", self.bass_pulse
            )
            unreal.MaterialEditingLibrary.set_material_parameter_collection_scalar_variable(
                mpc, "HarmonicRippleFreq", self.ripple_freq
            )
            unreal.MaterialEditingLibrary.set_material_parameter_collection_scalar_variable(
                mpc, "HarmonicRippleAmp", self.bass_pulse * 0.2
            )

    def stop(self):
        self.running = False
        if self.sock:
            self.sock.close()

if __name__ == "__main__":
    controller = HarmonicSynestheticGravityController()
    controller.start_listening()
