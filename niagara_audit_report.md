# Niagara VFX Automated QA & Profiling Audit Report

**Generated**: `2026-08-04T14:04:14.235332+00:00`  
**Execution Environment**: `Standalone Sentinel Python`  

## Executive Summary

| Metric | Count | Status |
| :--- | :--- | :--- |
| **Total Systems Scanned** | `40` | OK |
| **Clean Systems (No Violations)** | `39` | INFO |
| **Flagged Systems** | `1` | ACTION REQUIRED |
| **Critical CPU Spawn Rate Violations (>10k/s)** | `1` | CRITICAL |
| **Missing Fixed Bounds Violations** | `1` | WARNING |

## System Audit Findings

### Asset: `NS_UnoptimizedTest`
- **Package Path**: `/Game/EnvSandbox/VFX/Systems/NS_UnoptimizedTest`
- **Violations Count**: `2`

| Severity | Emitter | Rule | Issue Description | Remediation Recommendation |
| :--- | :--- | :--- | :--- | :--- |
| **CRITICAL** | `UnoptimizedCPUEmitter` | `CPU_SPAWN_RATE_THRESHOLD` | CPU-bound emitter 'UnoptimizedCPUEmitter' has spawn rate (15,000/sec) exceeding maximum threshold (10,000/sec) | Switch emitter Sim Target to GPUComputeSim or reduce spawn rate below 10,000/sec. |
| **WARNING** | `UnoptimizedCPUEmitter` | `FIXED_BOUNDS_MISSING` | Missing fixed bounds (Dynamic bounds active for emitter 'UnoptimizedCPUEmitter') | Enable 'Fixed Bounds' in System or Emitter properties to avoid CPU recalculation stalls. |

## Automated Remediation Checklist

1. **CPUSim Spawn Rate Threshold (> 10,000/sec)**:
   - Open system in Niagara Editor -> Select emitter -> Details -> Emitter Properties.
   - Change `Sim Target` from `CPUSim` to `GPUComputeSim` for high-count emitters.
2. **Fixed Bounds Check**:
   - Open Niagara System Properties -> Check `Fixed Bounds` checkbox.
   - Set suitable min/max bounds box to prevent dynamic CPU bounding box recalculation per frame.
