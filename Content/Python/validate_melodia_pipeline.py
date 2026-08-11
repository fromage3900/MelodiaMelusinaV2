"""
Quality Validation Module for Melodia Pipeline
Validate texture outputs against quality standards

Usage:
    from validate_melodia_pipeline import PipelineValidator
    
    validator = PipelineValidator()
    report = validator.validate_texture_set(textures)
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Tuple


class ValidationSeverity(Enum):
    """Severity levels for validation issues."""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class ValidationCategory(Enum):
    """Categories of validation checks."""
    RESOLUTION = "resolution"
    CHANNEL_LAYOUT = "channel_layout"
    COMPRESSION = "compression"
    FILE_SIZE = "file_size"
    COLOR_SPACE = "color_space"
    NORMAL_MAP = "normal_map"
    CONSISTENCY = "consistency"


@dataclass
class ValidationIssue:
    """Single validation issue."""
    category: ValidationCategory
    severity: ValidationSeverity
    message: str
    texture_path: Optional[Path] = None
    parameter: Optional[str] = None
    expected: Optional[str] = None
    actual: Optional[str] = None
    suggestion: Optional[str] = None


@dataclass
class ValidationReport:
    """Complete validation report."""
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    validation_time: float = 0.0
    total_textures: int = 0
    passed_textures: int = 0
    failed_textures: int = 0
    warning_count: int = 0
    error_count: int = 0
    critical_count: int = 0
    issues: List[ValidationIssue] = field(default_factory=list)
    
    def add_issue(self, issue: ValidationIssue):
        """Add validation issue to report."""
        self.issues.append(issue)
        
        if issue.severity == ValidationSeverity.WARNING:
            self.warning_count += 1
        elif issue.severity == ValidationSeverity.ERROR:
            self.error_count += 1
        elif issue.severity == ValidationSeverity.CRITICAL:
            self.critical_count += 1
    
    def is_valid(self) -> bool:
        """Check if validation passed (no errors or critical issues)."""
        return self.error_count == 0 and self.critical_count == 0
    
    def get_issues_by_severity(self, severity: ValidationSeverity) -> List[ValidationIssue]:
        """Get issues filtered by severity."""
        return [issue for issue in self.issues if issue.severity == severity]
    
    def get_issues_by_category(self, category: ValidationCategory) -> List[ValidationIssue]:
        """Get issues filtered by category."""
        return [issue for issue in self.issues if issue.category == category]
    
    def to_dict(self) -> Dict:
        """Convert report to dictionary."""
        return {
            "timestamp": self.timestamp.isoformat(),
            "validation_time": self.validation_time,
            "total_textures": self.total_textures,
            "passed_textures": self.passed_textures,
            "failed_textures": self.failed_textures,
            "warning_count": self.warning_count,
            "error_count": self.error_count,
            "critical_count": self.critical_count,
            "is_valid": self.is_valid(),
            "issues": [
                {
                    "category": issue.category.value,
                    "severity": issue.severity.value,
                    "message": issue.message,
                    "texture_path": str(issue.texture_path) if issue.texture_path else None,
                    "parameter": issue.parameter,
                    "expected": issue.expected,
                    "actual": issue.actual,
                    "suggestion": issue.suggestion
                }
                for issue in self.issues
            ]
        }
    
    def save(self, output_path: Path):
        """Save report to JSON file."""
        with open(output_path, 'w') as f:
            json.dump(self.to_dict(), f, indent=2)


class PipelineValidator:
    """Validate pipeline outputs against quality standards."""
    
    # Quality standards
    TARGET_RESOLUTIONS = [512, 1024, 2048, 4096]
    MAX_FILE_SIZE_MB = 16  # Maximum file size in MB
    ACCEPTABLE_FORMATS = ['.png', '.jpg', '.jpeg', '.tiff', '.tif', '.exr', '.tga']
    
    # Normal map validation
    NORMAL_MAP_INDICATORS = ['normal', 'nrm', '_n_', 'norm']
    NORMAL_VECTOR_RANGE = (-1.0, 1.0)
    
    def __init__(self):
        self.report = ValidationReport()
    
    def validate_texture_set(self, textures: Dict[str, Path]) -> ValidationReport:
        """Validate complete texture set."""
        import time
        
        start_time = time.time()
        self.report = ValidationReport()
        self.report.total_textures = len(textures)
        
        for texture_name, texture_path in textures.items():
            try:
                self._validate_single_texture(texture_name, texture_path)
                self.report.passed_textures += 1
            except Exception as e:
                self.report.failed_textures += 1
                self.report.add_issue(ValidationIssue(
                    category=ValidationCategory.CONSISTENCY,
                    severity=ValidationSeverity.ERROR,
                    message=f"Failed to validate texture: {str(e)}",
                    texture_path=texture_path
                ))
        
        # Validate consistency across texture set
        self._validate_texture_set_consistency(textures)
        
        self.report.validation_time = time.time() - start_time
        return self.report
    
    def _validate_single_texture(self, name: str, path: Path):
        """Validate single texture file."""
        if not path.exists():
            self.report.add_issue(ValidationIssue(
                category=ValidationCategory.CONSISTENCY,
                severity=ValidationSeverity.CRITICAL,
                message=f"Texture file does not exist",
                texture_path=path
            ))
            return
        
        # Check file format
        self._validate_file_format(path)
        
        # Check resolution
        self._validate_resolution(path)
        
        # Check file size
        self._validate_file_size(path)
        
        # Check normal map if applicable
        if self._is_normal_map(name):
            self._validate_normal_map(path)
    
    def _validate_file_format(self, path: Path):
        """Validate file format."""
        if path.suffix.lower() not in self.ACCEPTABLE_FORMATS:
            self.report.add_issue(ValidationIssue(
                category=ValidationCategory.COMPRESSION,
                severity=ValidationSeverity.WARNING,
                message=f"Uncommon file format: {path.suffix}",
                texture_path=path,
                suggestion="Consider using PNG or EXR for better quality"
            ))
    
    def _validate_resolution(self, path: Path):
        """Validate texture resolution."""
        # Placeholder - implement with PIL/Pillow
        resolution = self._get_resolution(path)
        
        if resolution:
            width, height = resolution
            
            # Check power-of-two
            if not self._is_power_of_two(width) or not self._is_power_of_two(height):
                self.report.add_issue(ValidationIssue(
                    category=ValidationCategory.RESOLUTION,
                    severity=ValidationSeverity.ERROR,
                    message=f"Resolution is not power-of-two: {width}x{height}",
                    texture_path=path,
                    expected="Power-of-two (512, 1024, 2048, 4096)",
                    actual=f"{width}x{height}",
                    suggestion="Resize to nearest power-of-two resolution"
                ))
            
            # Check against target resolutions
            if width not in self.TARGET_RESOLUTIONS or height not in self.TARGET_RESOLUTIONS:
                self.report.add_issue(ValidationIssue(
                    category=ValidationCategory.RESOLUTION,
                    severity=ValidationSeverity.WARNING,
                    message=f"Resolution not in target list: {width}x{height}",
                    texture_path=path,
                    expected=f"One of {self.TARGET_RESOLUTIONS}",
                    actual=f"{width}x{height}",
                    suggestion="Consider using standard resolution for optimization"
                ))
    
    def _validate_file_size(self, path: Path):
        """Validate file size."""
        file_size_mb = path.stat().st_size / (1024 * 1024)
        
        if file_size_mb > self.MAX_FILE_SIZE_MB:
            self.report.add_issue(ValidationIssue(
                category=ValidationCategory.FILE_SIZE,
                severity=ValidationSeverity.WARNING,
                message=f"File size exceeds recommended limit: {file_size_mb:.2f}MB",
                texture_path=path,
                expected=f"< {self.MAX_FILE_SIZE_MB}MB",
                actual=f"{file_size_mb:.2f}MB",
                suggestion="Consider compression or lower resolution"
            ))
    
    def _validate_normal_map(self, path: Path):
        """Validate normal map specifics."""
        # Placeholder - implement with PIL/Pillow
        # Check for proper normal map encoding
        # Check vector ranges
        # Check for normal map artifacts
        
        self.report.add_issue(ValidationIssue(
            category=ValidationCategory.NORMAL_MAP,
            severity=ValidationSeverity.INFO,
            message="Normal map validation - placeholder implementation",
            texture_path=path
        ))
    
    def _validate_texture_set_consistency(self, textures: Dict[str, Path]):
        """Validate consistency across texture set."""
        if not textures:
            return
        
        # Check that all textures have consistent resolutions
        resolutions = {}
        for name, path in textures.items():
            resolution = self._get_resolution(path)
            if resolution:
                resolutions[name] = resolution
        
        if resolutions:
            unique_resolutions = set(resolutions.values())
            if len(unique_resolutions) > 1:
                self.report.add_issue(ValidationIssue(
                    category=ValidationCategory.CONSISTENCY,
                    severity=ValidationSeverity.WARNING,
                    message=f"Inconsistent resolutions across texture set: {unique_resolutions}",
                    suggestion="Consider standardizing resolutions for consistency"
                ))
    
    def _is_normal_map(self, name: str) -> bool:
        """Check if texture is a normal map based on name."""
        name_lower = name.lower()
        return any(indicator in name_lower for indicator in self.NORMAL_MAP_INDICATORS)
    
    def _get_resolution(self, path: Path) -> Optional[Tuple[int, int]]:
        """Get texture resolution."""
        # Placeholder - implement with PIL/Pillow
        try:
            from PIL import Image
            with Image.open(path) as img:
                return img.size
        except ImportError:
            # Fallback if PIL not available
            return None
        except Exception:
            return None
    
    def _is_power_of_two(self, n: int) -> bool:
        """Check if number is power of two."""
        return n > 0 and (n & (n - 1)) == 0
    
    def validate_parameter(self, param_name: str, value: float, min_val: float, max_val: float) -> bool:
        """Validate single parameter value."""
        if not (min_val <= value <= max_val):
            self.report.add_issue(ValidationIssue(
                category=ValidationCategory.CONSISTENCY,
                severity=ValidationSeverity.ERROR,
                message=f"Parameter value out of range: {param_name}",
                parameter=param_name,
                expected=f"{min_val} - {max_val}",
                actual=str(value),
                suggestion=f"Adjust {param_name} to valid range"
            ))
            return False
        return True
    
    def validate_preset(self, preset_name: str, preset_data: Dict) -> bool:
        """Validate preset configuration."""
        issues_found = False
        
        # Check required fields
        required_fields = ["name", "description", "params"]
        for field in required_fields:
            if field not in preset_data:
                self.report.add_issue(ValidationIssue(
                    category=ValidationCategory.CONSISTENCY,
                    severity=ValidationSeverity.ERROR,
                    message=f"Missing required field in preset: {field}",
                    parameter=preset_name
                ))
                issues_found = True
        
        # Validate parameters
        if "params" in preset_data:
            for param_name, param_value in preset_data["params"].items():
                if not isinstance(param_value, (int, float)):
                    self.report.add_issue(ValidationIssue(
                        category=ValidationCategory.CONSISTENCY,
                        severity=ValidationSeverity.ERROR,
                        message=f"Parameter value must be numeric: {param_name}",
                        parameter=param_name,
                        actual=str(type(param_value))
                    ))
                    issues_found = True
        
        return not issues_found


class TextureQualityAnalyzer:
    """Analyze texture quality metrics."""
    
    @staticmethod
    def analyze_sharpness(texture_path: Path) -> float:
        """Analyze texture sharpness (placeholder)."""
        # Implement with PIL/OpenCV
        return 0.0
    
    @staticmethod
    def analyze_compression_artifacts(texture_path: Path) -> float:
        """Analyze compression artifacts (placeholder)."""
        # Implement with PIL/OpenCV
        return 0.0
    
    @staticmethod
    def analyze_color_distribution(texture_path: Path) -> Dict:
        """Analyze color distribution (placeholder)."""
        # Implement with PIL/OpenCV
        return {}
    
    @staticmethod
    def estimate_detail_level(texture_path: Path) -> str:
        """Estimate detail level (low/medium/high)."""
        # Implement with PIL/OpenCV
        return "medium"


# Convenience function for command-line usage
def main():
    """Command-line interface for validation."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Validate Melodia Pipeline Outputs")
    parser.add_argument("--input", "-i", required=True, help="Input texture directory")
    parser.add_argument("--output", "-o", help="Output validation report path")
    
    args = parser.parse_args()
    
    validator = PipelineValidator()
    
    # Scan directory for textures
    from pathlib import Path
    input_dir = Path(args.input)
    
    if not input_dir.exists():
        print(f"Error: Input directory not found: {input_dir}")
        return
    
    # Collect textures
    textures = {}
    for ext in ['.png', '.jpg', '.jpeg', '.tiff', '.tif', '.exr', '.tga']:
        for texture_path in input_dir.rglob(f"*{ext}"):
            textures[texture_path.stem] = texture_path
    
    print(f"Found {len(textures)} textures to validate")
    
    # Validate
    report = validator.validate_texture_set(textures)
    
    # Print summary
    print(f"\nValidation Report:")
    print(f"Total textures: {report.total_textures}")
    print(f"Passed: {report.passed_textures}")
    print(f"Failed: {report.failed_textures}")
    print(f"Warnings: {report.warning_count}")
    print(f"Errors: {report.error_count}")
    print(f"Critical: {report.critical_count}")
    print(f"Valid: {report.is_valid()}")
    
    # Save report
    if args.output:
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        report.save(output_path)
        print(f"\nReport saved to {output_path}")
    
    # Print issues
    if report.issues:
        print(f"\nIssues found:")
        for issue in report.issues:
            print(f"  [{issue.severity.value.upper()}] {issue.message}")
            if issue.texture_path:
                print(f"    File: {issue.texture_path}")
            if issue.suggestion:
                print(f"    Suggestion: {issue.suggestion}")


if __name__ == "__main__":
    main()