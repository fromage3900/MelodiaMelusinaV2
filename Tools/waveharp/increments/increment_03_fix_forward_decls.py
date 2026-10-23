"""Fix the header order: the forward declarations must come BEFORE the new types.

FMelodiaWaveHarpVfxBeat uses TSoftObjectPtr<UNiagaraSystem>, and the forward
declaration of UNiagaraSystem sat below it - so the struct did not compile. Move the
whole forward-declaration block above the new enums and structs.
"""
from pathlib import Path

H = Path(r"C:\EnvironmentPortfolio\BS_GodFile\Source\BS_GodFile\MelodiaIntegration\MelodiaWaveHarpCombatComponent.h")
text = H.read_text(encoding="utf-8")

BLOCK = """class ACharacter;
class APlayerController;
class UInputComponent;
class UStaticMeshComponent;
class UAnimMontage;
class USoundBase;
class USpringArmComponent;
class UMelodiaHybridEncounterComponent;
class UNiagaraSystem;
class UAnimSequence;
class USkeletalMesh;
class USkeletalMeshComponent;
class UStaticMesh;"""

if BLOCK not in text:
    raise SystemExit("ANCHOR MISSING: the forward declaration block")

text = text.replace(BLOCK + "\n", "", 1)

ANCHOR = "class UAnimNotify_MelodiaScytheHit;\n"
if ANCHOR not in text:
    raise SystemExit("ANCHOR MISSING: the notify forward declaration")
text = text.replace(ANCHOR, ANCHOR + "\n" + BLOCK + "\n", 1)

H.write_text(text, encoding="utf-8")
print("forward declarations moved above the new types")
