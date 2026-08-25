#!/usr/bin/env python
"""Breakdown Editor and Review System for TouchDesigner Networks.

This system provides tools for:
- Visual breakdown editing and analysis
- Component performance tracking
- Web integration validation
- Automated breakdown updates
- Review and approval workflows

Usage:
    python breakdown_editor.py --analyze <network_path>
    python breakdown_editor.py --update-website
    python breakdown_editor.py --review <network_path>
"""

import os
import json
import re
import time
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional
import argparse
from collections import defaultdict

PROJECT_ROOT = "G:/EnvironmentPortfolio/BS_GodFile"


class BreakdownEditor:
    def __init__(self):
        self.browser_data = {}
        self.analysis_cache = {}
        self.validation_rules = self._load_validation_rules()

    def _load_validation_rules(self) -> Dict[str, Any]:
        """Load validation rules from configuration."""
        return {
            "component_structure": {
                "min_components": 3,
                "allowed_types": ["TOP", "COMP", "MAT", "DAT", "SOP", "CHN", "VOP", "TOPSubnet"],
                "required_files": ["__init__.py", "index.py"]
            },
            "web_integration": {
                "required_mcp_adapters": ["blender_mcp_adapter.py", "surreal_arch_mcp_adapter.py"],
                "required_endpoints": ["/api/toc", "/api/ai_commands"],
                "required_schema_files": ["catalog_schema.json", "world_schema.json"]
            },
            "performance": {
                "max_frame_time_ms": 33,
                "target_fps": 60,
                "memory_threshold_mb": 1024
            },
            "assets": {
                "required_render_extensions": [".png", ".jpg", ".jpeg", ".webp"],
                "required_media_extensions": [".mov", ".mp4", ".avi"],
                "required_config_extensions": [".json", ".xml", ".fxh"]
            }
        }

    def analyze_network_structure(self, network_path: str) -> Dict[str, Any]:
        """Analyze TouchDesigner network structure comprehensively."""
        print(f"Analyzing network structure: {network_path}")
        
        analysis = {
            "timestamp": datetime.now().isoformat(),
            "network_path": network_path,
            "components": [],
            "files": [],
            "structure_score": 0,
            "findings": [],
            "recommendations": [],
            "validation": {}
        }
        
        try:
            network_dir = Path(network_path)
            
            # Analyze Python files
            python_files = list(network_dir.glob("*.py"))
            for py_file in python_files:
                component = self._analyze_python_file(py_file)
                analysis["components"].append(component)
                
            # Analyze configuration files
            config_files = list(network_dir.glob("*.json")) + \
                         list(network_dir.glob("*.xml")) + \
                         list(network_dir.glob("*.cfg"))
            for config_file in config_files:
                config = self._analyze_config_file(config_file)
                analysis["components"].append(config)
                
            # Analyze data files
            data_files = list(network_dir.glob("*.dat")) + \
                        list(network_dir.glob("*.bge")) + \
                        list(network_dir.glob("*.toe"))
            for data_file in data_files:
                data = self._analyze_data_file(data_file)
                analysis["components"].append(data)
                
            # Analyze scripts
            script_files = list(network_dir.glob("*_ops.py")) + \
                          list(network_dir.glob("*_bridge.py")) + \
                          list(network_dir.glob("*integration.py"))
            for script_file in script_files:
                script = self._analyze_script_file(script_file)
                analysis["components"].append(script)
                
            # Analyze documentation
            doc_files = list(network_dir.glob("README*")) + \
                       list(network_dir.glob("*.md")) + \
                       list(network_dir.glob("*.rst"))
            for doc_file in doc_files:
                doc = self._analyze_documentation(doc_file)
                analysis["components"].append(doc)
                
            # Analyze shared directories
            if (network_dir / "shared").exists():
                shared_analysis = self._analyze_shared_directory(network_dir / "shared")
                analysis["components"].extend(shared_analysis)
                
            # Validate structure
            analysis["validation"] = self._validate_structure(analysis["components"], network_dir)
                
            # Calculate score
            analysis["structure_score"] = self._calculate_structure_score(analysis["components"], analysis["validation"])
                
            # Generate findings and recommendations
            analysis["findings"] = self._generate_findings(analysis["components"], analysis["validation"])
            analysis["recommendations"] = self._generate_recommendations(analysis["components"], analysis["structure_score"])
                
        except Exception as e:
            analysis["findings"].append({
                "type": "ERROR",
                "severity": "CRITICAL",
                "message": f"Analysis error: {str(e)}",
                "source": "system"
            })
                
        return analysis

    def _analyze_python_file(self, file_path: Path) -> Dict[str, Any]:
        """Analyze Python file for component information."""
        component = {
            "type": "python",
            "name": file_path.stem,
            "path": str(file_path),
            "size": file_path.stat().st_size,
            "modified": datetime.fromtimestamp(file_path.stat().st_mtime).isoformat(),
            "analysis": {}
        }
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            component["analysis"] = {
                "classes": len(re.findall(r'^class\s+\w+', content, re.MULTILINE)),
                "functions": len(re.findall(r'^def\s+\w+', content, re.MULTILINE)),
                "imports": len(re.findall(r'^import\s+\w+', content, re.MULTILINE)),
                "exports": len(re.findall(r'^__all__\s*=', content)),
                "has_main": "if __name__ == '__main__':" in content,
                "line_count": len(content.splitlines()),
                "has_docstrings": len(re.findall(r'\"\"\"[^\"]*\"\"\"', content)) > 0,
                "has_comments": len(re.findall(r'^\s*#.*', content, re.MULTILINE)) > 0
            }
                
        except Exception as e:
            component["analysis"]["error"] = str(e)
                
        return component

    def _analyze_config_file(self, file_path: Path) -> Dict[str, Any]:
        """Analyze configuration file."""
        component = {
            "type": "config",
            "name": file_path.stem,
            "path": str(file_path),
            "size": file_path.stat().st_size,
            "modified": datetime.fromtimestamp(file_path.stat().st_mtime).isoformat(),
            "format": file_path.suffix.lower()
        }
        
        try:
            if file_path.suffix.lower() == '.json':
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    component["structure"] = {
                        "type": type(data),
                        "keys_count": len(data) if isinstance(data, dict) else 0,
                        "has_validation": "version" in str(data).lower() or "schema" in str(data).lower()
                    }
            elif file_path.suffix.lower() in ['.xml', '.cfg']:
                component["structure"] = {"format": file_path.suffix.upper()}
        except Exception as e:
            component["error"] = str(e)
                
        return component

    def _analyze_data_file(self, file_path: Path) -> Dict[str, Any]:
        """Analyze data file."""
        component = {
            "type": "data",
            "name": file_path.stem,
            "path": str(file_path),
            "size": file_path.stat().st_size,
            "modified": datetime.fromtimestamp(file_path.stat().st_mtime).isoformat(),
            "format": file_path.suffix.lower()
        }
        
        try:
            if file_path.suffix.lower() in ['.dat']:
                component["analysis"] = {
                    "is_data_file": True,
                    "format": "TouchDesigner DAT"
                }
            elif file_path.suffix.lower() in ['.bge']:
                component["analysis"] = {
                    "is_backstage_file": True,
                    "format": "TouchDesigner Backstage"
                }
            elif file_path.suffix.lower() in ['.toe']:
                component["analysis"] = {
                    "is_network_file": True,
                    "format": "TouchDesigner Network"
                }
        except Exception as e:
            component["error"] = str(e)
                
        return component

    def _analyze_script_file(self, file_path: Path) -> Dict[str, Any]:
        """Analyze script file."""
        component = {
            "type": "script",
            "name": file_path.stem,
            "path": str(file_path),
            "size": file_path.stat().st_size,
            "modified": datetime.fromtimestamp(file_path.stat().st_mtime).isoformat(),
            "format": file_path.suffix.lower()
        }
        
        try:
            script_types = {
                "_ops.py": "Operator/Driver Script",
                "_bridge.py": "Bridge/Adapter Script",
                "_integration.py": "Integration Script"
            }
            
            component["analysis"] = {
                "script_type": script_types.get(file_path.name, "Unknown Script Type"),
                "likely_usage": self._determine_script_usage(file_path.stem)
            }
                
        except Exception as e:
            component["error"] = str(e)
                
        return component

    def _analyze_documentation(self, file_path: Path) -> Dict[str, Any]:
        """Analyze documentation file."""
        component = {
            "type": "documentation",
            "name": file_path.stem,
            "path": str(file_path),
            "size": file_path.stat().st_size,
            "modified": datetime.fromtimestamp(file_path.stat().st_mtime).isoformat(),
            "format": "documentation"
        }
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            component["analysis"] = {
                "has_markdown": file_path.suffix.lower() == '.md',
                "has_rst": file_path.suffix.lower() in ['.rst', '.txt'],
                "content_length": len(content),
                "has_toc": "Table of Contents" in content or "##" in content,
                "has_examples": "example" in content.lower(),
                "has_api_docs": "API" in content or "function" in content.lower()
            }
                
        except Exception as e:
            component["error"] = str(e)
                
        return component

    def _analyze_shared_directory(self, shared_dir: Path) -> List[Dict[str, Any]]:
        """Analyze shared directory contents."""
        components = []
        
        for item in shared_dir.iterdir():
            if item.is_file():
                component = {
                    "type": "shared_file",
                    "name": item.name,
                    "path": str(item),
                    "size": item.stat().st_size,
                    "modified": datetime.fromtimestamp(item.stat().st_mtime).isoformat()
                }
                components.append(component)
            elif item.is_dir():
                components.extend(self._analyze_shared_directory(item))
                
        return components

    def _determine_script_usage(self, script_name: str) -> str:
        """Determine likely script usage based on name."""
        script_name_lower = script_name.lower()
        
        if "blender" in script_name_lower:
            return "Blender Integration"
        elif "melodia" in script_name_lower:
            return "Melodia System Integration"
        elif "unreal" in script_name_lower or "ue" in script_name_lower:
            return "Unreal Engine Integration"
        elif "bridge" in script_name_lower:
            return "Bridge/Adapter Function"
        elif "pipeline" in script_name_lower:
            return "Pipeline Orchestration"
        elif "catalog" in script_name_lower:
            return "Asset Catalog Management"
        else:
            return "General Purpose Script"

    def _validate_structure(self, components: List[Dict[str, Any]], network_dir: Path) -> Dict[str, Any]:
        """Validate network structure against rules."""
        validation = {
            "passed": True,
            "failed_checks": [],
            "passed_checks": [],
            "check_results": {}
        }
        
        rules = self.validation_rules["component_structure"]
        
        # Check minimum components
        python_files = [c for c in components if c["type"] == "python"]
        if len(python_files) >= rules["min_components"]:
            validation["passed_checks"].append({
                "name": "Component Count",
                "status": "PASS",
                "message": f"Found {len(python_files)} Python files (>= {rules['min_components']})"
            })
        else:
            validation["failed_checks"].append({
                "name": "Component Count",
                "status": "FAIL",
                "message": f"Found {len(python_files)} Python files (< {rules['min_components']})"
            })
            validation["passed"] = False
            
        # Check essential files
        essential_files_exist = True
        for essential_file in rules["required_files"]:
            if not (network_dir / essential_file).exists():
                essential_files_exist = False
                validation["failed_checks"].append({
                    "name": f"Essential File: {essential_file}",
                    "status": "FAIL",
                    "message": f"Missing essential file: {essential_file}"
                })
            else:
                validation["passed_checks"].append({
                    "name": f"Essential File: {essential_file}",
                    "status": "PASS",
                    "message": f"Found essential file: {essential_file}"
                })
                
        if not essential_files_exist:
            validation["passed"] = False
            
        # Check component types
        component_types = [c["type"] for c in components]
        unique_types = set(component_types)
        if len(unique_types) >= 3:
            validation["passed_checks"].append({
                "name": "Component Diversity",
                "status": "PASS",
                "message": f"Found diverse component types: {', '.join(unique_types)}"
            })
        else:
            validation["failed_checks"].append({
                "name": "Component Diversity",
                "status": "WARN",
                "message": f"Limited component types: {', '.join(unique_types)}"
            })
            
        return validation

    def _calculate_structure_score(self, components: List[Dict[str, Any]], validation: Dict[str, Any]) -> int:
        """Calculate overall structure score."""
        base_score = 0
        
        # Base score for existing components
        python_score = min(len([c for c in components if c["type"] == "python"]) * 10, 100)
        config_score = min(len([c for c in components if c["type"] == "config"]) * 15, 100)
        data_score = min(len([c for c in components if c["type"] == "data"]) * 10, 100)
        script_score = min(len([c for c in components if c["type"] == "script"]) * 10, 100)
        doc_score = min(len([c for c in components if c["type"] == "documentation"]) * 5, 100)
        
        base_score = python_score + config_score + data_score + script_score + doc_score
        
        # Validation adjustments
        if validation["passed"]:
            base_score += 50
            
        return min(base_score, 100)

    def _generate_findings(self, components: List[Dict[str, Any]], validation: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate findings from analysis."""
        findings = []
        
        # Structure findings
        if validation["failed_checks"]:
            for check in validation["failed_checks"]:
                if check["status"] in ["FAIL", "ERROR"]:
                    findings.append({
                        "type": "STRUCTURE_ISSUE",
                        "severity": "HIGH" if check["status"] == "FAIL" else "CRITICAL",
                        "message": f"{check['name']}: {check['message']}",
                        "location": "structure",
                        "impact": "affects_network_functionality"
                    })
                    
        # Component-specific findings
        python_components = [c for c in components if c["type"] == "python"]
        for component in python_components:
            analysis = component.get("analysis", {})
            if analysis.get("error"):
                findings.append({
                    "type": "COMPONENT_ERROR",
                    "severity": "MEDIUM",
                    "message": f"Analysis error in {component['name']}: {analysis['error']}",
                    "location": component['path'],
                    "impact": "data_loss"
                })
                
            if analysis.get("line_count", 0) > 500:
                findings.append({
                    "type": "COMPLEXITY_WARNING",
                    "severity": "LOW",
                    "message": f"Large Python file {component['name']} ({analysis['line_count']} lines)",
                    "location": component['path'],
                    "impact": "maintenance_overhead"
                })
                
        return findings

    def _generate_recommendations(self, components: List[Dict[str, Any]], score: int) -> List[str]:
        """Generate recommendations based on analysis."""
        recommendations = []
        
        if score < 70:
            recommendations.extend([
                "Add missing essential Python files (__init__.py, index.py)",
                "Increase component count to meet minimum requirements",
                "Add comprehensive documentation"
            ])
            
        config_components = [c for c in components if c["type"] == "config"]
        if not config_components:
            recommendations.append("Add configuration files (JSON, XML, CFG) for proper network management")
            
        script_components = [c for c in components if c["type"] == "script"]
        if len(script_components) < 2:
            recommendations.append("Add operator scripts (_ops.py, _bridge.py) for TouchDesigner integration")
            
        # Check for specific patterns
        python_components = [c for c in components if c["type"] == "python"]
        for component in python_components:
            analysis = component.get("analysis", {})
            if not analysis.get("has_docstrings", False):
                recommendations.append(f"Add docstrings to {component['name']}")
            if not analysis.get("has_comments", False):
                recommendations.append(f"Add comments to {component['name']} for better documentation")
                
        return recommendations

    def generate_breakdown_report(self, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Generate comprehensive breakdown report."""
        report = {
            "title": "TouchDesigner Network Breakdown Report",
            "timestamp": datetime.now().isoformat(),
            "network_analysis": analysis,
            "summary": {
                "total_components": len(analysis.get("components", [])),
                "score": analysis.get("structure_score", 0),
                "status": self._get_score_status(analysis.get("structure_score", 0)),
                "findings_count": len(analysis.get("findings", [])),
                "recommendations_count": len(analysis.get("recommendations", []))
            },
            "detailed_analysis": {
                "components_by_type": self._categorize_components(analysis.get("components", [])),
                "file_structure": self._generate_file_structure(analysis.get("components", [])),
                "technical_details": self._extract_technical_details(analysis.get("components", []))
            },
            "quality_metrics": self._calculate_quality_metrics(analysis)
        }
        
        return report

    def _get_score_status(self, score: int) -> str:
        """Get status based on score."""
        if score >= 90:
            return "EXCELLENT"
        elif score >= 80:
            return "GOOD"
        elif score >= 70:
            return "SATISFACTORY"
        elif score >= 60:
            return "NEEDS_IMPROVEMENT"
        elif score >= 50:
            return "POOR"
        else:
            return "CRITICAL"

    def _categorize_components(self, components: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Categorize components by type and analyze."""
        categories = {}
        type_stats = defaultdict(list)
        
        for component in components:
            type_stats[component["type"]].append(component)
            
        for component_type, type_components in type_stats.items():
            category_info = {
                "count": len(type_components),
                "total_size": sum(c.get("size", 0) for c in type_components),
                "average_size": sum(c.get("size", 0) for c in type_components) / len(type_components) if type_components else 0,
                "latest_modified": max(
                    (c.get("modified", "") for c in type_components if c.get("modified")),
                    key=lambda x: x if x else "",
                    default=""
                ),
                "components": []
            }
            
            # Add details for each component
            for component in type_components[:10]:  # Limit details for readability
                category_info["components"].append({
                    "name": component["name"],
                    "path": component["path"],
                    "size": component.get("size", 0),
                    "modified": component.get("modified", "")
                })
                
            if len(type_components) > 10:
                category_info["components"].append({
                    "name": f"... and {len(type_components) - 10} more",
                    "path": f"{len(type_components) - 10} additional files",
                    "type": "summary"
                })
                
            categories[component_type] = category_info
            
        return categories

    def _generate_file_structure(self, components: List[Dict[str, Any]]) -> List[str]:
        """Generate file structure tree."""
        structure = []
        
        # Group by type
        by_type = defaultdict(list)
        for component in components:
            by_type[component["type"]].append(component)
            
        for component_type in sorted(by_type.keys()):
            structure.append(f"\n=== {component_type.upper()} ===")
            for component in sorted(by_type[component_type], key=lambda x: x["name"]):
                structure.append(f"  ├─ {component['name']}.{component.get('format', '')}")
                if component.get("analysis"):
                    for key, value in component["analysis"].items():
                        if isinstance(value, bool):
                            structure.append(f"      ├─ {key}: {'*' if value else '*'}")
                        elif isinstance(value, (int, float)):
                            structure.append(f"      ├─ {key}: {value}")
                        elif key != "error" and value not in ["", None]:
                            structure.append(f"      ├─ {key}: {str(value)[:50]}")
                                
        return structure

    def _extract_technical_details(self, components: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Extract technical details from components."""
        details = {
            "total_lines": 0,
            "total_size": 0,
            "latest_update": "",
            "most_complex": {},
            "code_stats": {}
        }
        
        for component in components:
            details["total_size"] += component.get("size", 0)
            
            if component["type"] == "python":
                details["total_lines"] += component.get("analysis", {}).get("line_count", 0)
                details["code_stats"][component["name"]] = {
                    "lines": component.get("analysis", {}).get("line_count", 0),
                    "classes": component.get("analysis", {}).get("classes", 0),
                    "functions": component.get("analysis", {}).get("functions", 0),
                    "imports": component.get("analysis", {}).get("imports", 0)
                }
                
            # Track latest update
            modified = component.get("modified", "")
            if modified and (not details["latest_update"] or modified > details["latest_update"]):
                details["latest_update"] = modified
                
        details["average_lines_per_file"] = details["total_lines"] / max(1, len([c for c in components if c["type"] == "python"]))
        details["average_size_kb"] = details["total_size"] / 1024 / max(1, len(components))
        
        # Find most complex file
        if details["code_stats"]:
            most_complex = max(details["code_stats"].items(), key=lambda x: x[1]["lines"])
            details["most_complex"] = {
                "file": most_complex[0],
                "lines": most_complex[1]["lines"],
                "classes": most_complex[1]["classes"],
                "functions": most_complex[1]["functions"]
            }
            
        return details

    def _calculate_quality_metrics(self, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate quality metrics."""
        metrics = {
            "completeness_score": 0,
            "documentation_score": 0,
            "structure_score": 0,
            "technical_health": 0,
            "web_readiness": 0
        }
        
        components = analysis.get("components", [])
        
        # Component completeness
        total_possible = len(components) * 10  # Each component gets 10 points
        earned_points = sum(
            min(c.get("analysis", {}).get("classes", 0) * 2 + 
                c.get("analysis", {}).get("functions", 0) + 
                min(5 if c.get("analysis", {}).get("has_docstrings") else 0) +
                min(3 if c.get("analysis", {}).get("has_comments") else 0),
                10
        ) for c in components if c["type"] == "python"
        )
        metrics["completeness_score"] = (earned_points / total_possible * 100) if total_possible > 0 else 0
        
        # Documentation score
        doc_count = len([c for c in components if c["type"] == "documentation"])
        metrics["documentation_score"] = min(doc_count * 20, 100)
        
        # Structure score (use existing score)
        metrics["structure_score"] = analysis.get("structure_score", 0)
        
        # Technical health (based on code quality)
        technical_issues = 0
        for c in components:
            if c["type"] == "python":
                analysis_data = c.get("analysis", {})
                if analysis_data.get("line_count", 0) > 1000:
                    technical_issues += 1
        metrics["technical_health"] = max(0, 100 - (technical_issues * 5))
        
        # Web readiness (check for web-related files)
        web_files = len([c for c in components if "web" in c.get("name", "").lower()])
        mcp_files = len([c for c in components if "mcp" in c.get("name", "").lower()])
        validation_files = len([c for c in components if "validation" in c.get("name", "").lower()])
        metrics["web_readiness"] = min((web_files + mcp_files + validation_files) * 25, 100)
        
        # Overall score (weighted average)
        weights = {
            "completeness": 0.25,
            "documentation": 0.15,
            "structure": 0.25,
            "technical_health": 0.20,
            "web_readiness": 0.15
        }
        
        metrics["overall"] = (
            metrics["completeness_score"] * weights["completeness"] +
            metrics["documentation_score"] * weights["documentation"] +
            metrics["structure_score"] * weights["structure"] +
            metrics["technical_health"] * weights["technical_health"] +
            metrics["web_readiness"] * weights["web_readiness"]
        )
        
        return metrics

    def analyze_web_integration(self, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze web integration capabilities."""
        print("Analyzing web integration...")
        
        web_analysis = {
            "timestamp": datetime.now().isoformat(),
            "integration_score": 0,
            "web_capabilities": [],
            "missing_integrations": [],
            "recommendations": []
        }
        
        components = analysis.get("components", [])
        
        # Check for required web integration components
        required_patterns = [
            ("blender_mcp_adapter.py", "Blender MCP Adapter"),
            ("surreal_arch_mcp_adapter.py", "Surreal Architecture MCP Adapter"),
            ("agent_bridge_mcp.py", "Agent Bridge MCP"),
            ("generate_web_manifest.py", "Web Manifest Generator"),
            ("ai_tool_router.py", "AI Tool Router")
        ]
        
        found_components = []
        for pattern, description in required_patterns:
            found = any(
                pattern in c.get("path", "") or pattern in c["name"]
                for c in components
            )
            if found:
                found_components.append(description)
                web_analysis["web_capabilities"].append({
                    "name": description,
                    "status": "AVAILABLE",
                    "impact": "high"
                })
            else:
                web_analysis["missing_integrations"].append({
                    "name": description,
                    "priority": "high",
                    "impact": "limits_web_accessibility"
                })
                
        # Calculate integration score
        web_score = (len(found_components) / len(required_patterns)) * 100
        web_analysis["integration_score"] = web_score
        
        # Generate recommendations
        if web_score < 80:
            web_analysis["recommendations"].extend([
                "Implement missing web integration adapters",
                "Add web manifest generation capabilities",
                "Create unified AI tool router",
                "Set up real-time web synchronization"
            ])
            
        return web_analysis

    def update_web_content(self) -> Dict[str, Any]:
        """Update website content with new breakdown data."""
        print("Updating website content...")
        
        result = {
            "timestamp": datetime.now().isoformat(),
            "update_status": "SUCCESS",
            "updated_files": [],
            "errors": []
        }
        
        try:
            # Create/update validation report
            report_path = Path(PROJECT_ROOT) / "Saved" / "Audit" / "touchdesigner_validation_report.json"
            if report_path.exists():
                with open(report_path, 'r', encoding='utf-8') as f:
                    report_data = json.load(f)
                    
                # Update the report with breakdown data
                if "breakdown_analysis" not in report_data.get("validation_report", {}):
                    report_data["validation_report"]["breakdown_analysis"] = {
                        "generated": datetime.now().isoformat(),
                        "components_analyzed": report_data.get("validation_report", {}).get("categories", {}).get("components", 0),
                        "score": report_data.get("validation_report", {}).get("overall_score", 0)
                    }
                    
                # Save updated report
                with open(report_path, 'w', encoding='utf-8') as f:
                    json.dump(report_data, f, indent=2, ensure_ascii=False)
                    
                result["updated_files"].append(str(report_path))
                
        except Exception as e:
            result["update_status"] = "ERROR"
            result["errors"].append(f"Failed to update content: {str(e)}")
            
        return result

    def run_comprehensive_analysis(self, network_path: Optional[str] = None) -> Dict[str, Any]:
        """Run comprehensive analysis including web integration."""
        print("=" * 60)
        print("TOUCHDESIGNER BREAKDOWN EDITOR")
        print("=" * 60)
        
        analysis_results = {
            "network_analysis": None,
            "web_analysis": None,
            "breakdown_report": None,
            "update_results": None,
            "recommendations": []
        }
        
        # Analyze network structure
        if network_path:
            if not Path(network_path).exists():
                return {
                    "error": f"Network path does not exist: {network_path}",
                    "status": "FAILED"
                }
                
            analysis_results["network_analysis"] = self.analyze_network_structure(network_path)
            
        # Generate breakdown report
        if analysis_results["network_analysis"]:
            analysis_results["breakdown_report"] = self.generate_breakdown_report(
                analysis_results["network_analysis"]
            )
            
        # Analyze web integration
        analysis_results["web_analysis"] = self.analyze_web_integration(
            analysis_results["network_analysis"] or {}
        )
        
        # Update website content
        analysis_results["update_results"] = self.update_web_content()
        
        # Generate comprehensive recommendations
        analysis_results["recommendations"] = self._generate_comprehensive_recommendations(
            analysis_results
        )
        
        return analysis_results

    def _generate_comprehensive_recommendations(self, results: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate comprehensive recommendations."""
        recommendations = []
        
        # Structure recommendations
        if results["network_analysis"]:
            network_score = results["network_analysis"].get("structure_score", 0)
            if network_score < 70:
                recommendations.append({
                    "category": "NETWORK_STRUCTURE",
                    "priority": "HIGH",
                    "message": "Improve network structure for better maintainability",
                    "actions": [
                        "Add essential Python files (__init__.py, index.py)",
                        "Increase component diversity and documentation",
                        "Establish consistent naming conventions"
                    ]
                })
                
        # Web integration recommendations
        web_score = results.get("web_analysis", {}).get("integration_score", 0)
        if web_score < 80:
            recommendations.append({
                "category": "WEB_INTEGRATION",
                "priority": "HIGH",
                "message": "Enhance web integration capabilities",
                "actions": [
                    "Implement missing MCP adapters",
                    "Add web manifest generation",
                    "Create unified AI tool router",
                    "Set up real-time web synchronization"
                ]
            })
                
        # Update recommendations
        if results.get("update_results", {}).get("update_status") == "ERROR":
            recommendations.append({
                "category": "WEBSITE_UPDATES",
                "priority": "MEDIUM",
                "message": "Fix website update process",
                "actions": [
                    "Resolve content update errors",
                    "Implement backup mechanisms",
                    "Set up automated sync pipelines"
                ]
            })
                
        return recommendations


def save_breakdown_report(report: Dict[str, Any], output_path: str) -> None:
    """Save breakdown report to file."""
    try:
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        print(f"Report saved to: {output_path}")
    except Exception as e:
        print(f"Error saving report: {str(e)}")


def main():
    parser = argparse.ArgumentParser(
        description="TouchDesigner Breakdown Editor and Review System"
    )
    
    parser.add_argument(
        "--analyze",
        help="Path to TouchDesigner network to analyze"
    )
    
    parser.add_argument(
        "--review",
        help="Path to TouchDesigner network for review (includes validation)"
    )
    
    parser.add_argument(
        "--update-website",
        action="store_true",
        help="Update website content with analysis results"
    )
    
    parser.add_argument(
        "--output",
        default="G:/EnvironmentPortfolio/BS_GodFile/Saved/Audit/breakdown_report.json",
        help="Output path for breakdown report"
    )
    
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Minimal output (no progress messages)"
    )
    
    args = parser.parse_args()
    
    editor = BreakdownEditor()
    
    analysis_results = {}
    
    if args.analyze:
        if not args.quiet:
            print(f"Analyzing network: {args.analyze}")
        analysis_results = editor.run_comprehensive_analysis(args.analyze)
    elif args.review:
        if not args.quiet:
            print(f"Reviewing network: {args.review}")
        analysis_results = editor.run_comprehensive_analysis(args.review)
    else:
        parser.print_help()
        return
        
    # Save breakdown report
    if not args.quiet:
        print(f"\nAnalysis completed. Generating breakdown report...")
    
    save_breakdown_report(analysis_results, args.output)
    
    # Display summary
    if not args.quiet:
        print(f"\nBREAKDOWN ANALYSIS SUMMARY:")
        if analysis_results.get("breakdown_report"):
            summary = analysis_results["breakdown_report"]["summary"]
            print(f"  Components Analyzed: {summary['total_components']}")
            print(f"  Structure Score: {summary['score']}/100 ({summary['status']})")
            print(f"  Findings: {summary['findings_count']}")
            print(f"  Recommendations: {summary['recommendations_count']}")
            
        if analysis_results.get("web_analysis"):
            web_score = analysis_results["web_analysis"]["integration_score"]
            print(f"  Web Integration Score: {web_score}/100")
            
        if analysis_results.get("update_results"):
            status = analysis_results["update_results"]["update_status"]
            files = len(analysis_results["update_results"].get("updated_files", []))
            print(f"  Website Update: {status} ({files} files updated)")
            
        print(f"\nReport saved to: {args.output}")


if __name__ == "__main__":
    main()
