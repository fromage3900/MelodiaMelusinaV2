export const AZIMUTH_DEG = 24;
export const POLAR_DEG = 74;
export const RADIUS_M = 1.2;
export const TARGET = { x: 0, y: 0.02, z: 0 };
export const FOV_DEG = 28;
export const ROOT_ROTATION_X = -Math.PI / 2;

export const modelViewer = {
  orientation: '0deg 90deg 0deg',
  orbit: `${AZIMUTH_DEG}deg ${POLAR_DEG}deg ${RADIUS_M}m`,
  target: `${TARGET.x}m ${TARGET.y}m ${TARGET.z}m`,
  fov: `${FOV_DEG}deg`,
};

// Same 24° / 74° 3/4, mapped into Babylon's glTF frame after root X −PI/2.
// Radius is span-relative because Babylon does not share model-viewer's meter orbit.
export const babylon = {
  alpha: AZIMUTH_DEG * (Math.PI / 180),
  beta: POLAR_DEG * (Math.PI / 180),
  radiusOverSpan: 2.8,
  minRadius: 0.22,
  rootRotationX: ROOT_ROTATION_X,
};
