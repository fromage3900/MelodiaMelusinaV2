@echo off
:: Launch Painter with the Melodia SMS auto-build armed.
:: The plugin self-fires m.build_sms() ~20s after start, on whatever
:: texture set is OPEN. Open Mr. Sheep (or any .spp/FBX) first, or
:: re-run the console one-liner after the project loads:
::   import melodia_build_sms_handpaint as m; m.build_sms()
set MELUSINA_AUTO_BUILD_SMS=1
start "" "C:\Program Files\Adobe\Adobe Substance 3D Painter\Adobe Substance 3D Painter.exe"
