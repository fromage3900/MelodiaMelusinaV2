# Golden piano path (offline, non-canonical)
Run `python golden_piano_path.py [--seed --phi-mode --n-segments --scale --peak-fib]`; writes manifest + preview here.
Reuses `Content/Python/pcg_piano_layout.py` (walkable dims 110x520x30 / 64x320x36, gap 4); not edited.

## Design
- Each segment = one straight APCGPianoKeyboard (key identity = local-X order), so the winding path is a CHAIN of segments.
- White-key counts are Fibonacci up to a peak and back down: 5,8,13,8,5 (3 dropped: too short for radius >= 300).
- Heading turns by 360/phi^3 = 84.98 deg per joint (~ one quarter turn per phi growth in length, i.e. the polyline
  approximates r = a*phi^(theta/90deg)). Turn sign flips after the 13-key peak -> S/yin-yang shape, so the inward half
  never collides with the outward half. Other `phi_mode`: golden_angle (180-137.5077 = 42.49 deg), quarter (90).
- Joint: next segment starts 30 cm past the previous end along the old heading (visible, walkable gap).
  Adjacent ribbons (520 deep) overlap at the inner corner of a joint by design (same height 30; expect z-fighting there).
- MIDI: C4=60 upward; each segment starts/ends on a white key, next starts on the next white; wraps down by octaves if >108.
  Black key between segments is skipped (e.g. 67 -> 69).
- `seed`: even/odd = chirality, seed//2 % 8 * 45 deg = initial yaw. `scale` multiplies key dims and joint gap.

## Result (seed 0, phi_cubed, 5 segments)
62 keys (39 white, 23 black), path 4546 cm, extent 2000 x 2652 cm (inside 3000 box, re-centred on origin),
min turn radius 309 cm (fillet inscribed in half the shorter adjacent segment), non-adjacent overlap (every key rect,
20 cm clearance, SAT) = pass. 7 segments (3,5,8,13,8,5,3) gives 73 keys but fails radius (184 cm).

## Using the manifest
Spawn one APCGPianoKeyboard per segment at `anchor_xy_cm` (keys are centred on the actor origin), yaw = `yaw_deg`
(from +X toward +Y), first/last MIDI from the manifest. Z and level placement are left to the consumer.
