#!/usr/bin/env python
"""TouchDesigner Review and Validation System.

This system provides comprehensive review and validation tools for TouchDesigner
networks, renders, and integration with the web pipeline.

Features:
- Network structure validation
- Asset completeness checks
- Performance optimization recommendations
- Integration validation with MCP and web systems
- Automated review and scoring

Usage:
    python touchdesigner_validator.py --validate <network_path>
    python touchdesigner_validator.py --validate-all
    python touchdesigner_validator.py --review <network_path>
"""

import os
import json
import re
import time
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional
import argparse

PROJECT_ROOT = "C:/EnvironmentPortfolio/BS_GodFile"


class TouchDesignerValidator:
    def __init__(self):
        self.scores = {}
        self.findings = []
        self.recommendations = []
        self.total_weight = 0

    def validate_network_structure(self, network_path: str) -> Dict[str, Any]:
        """Validate TouchDesigner network structure."""
        print(f"Validating network: {network_path}")
        
        result = {
            "structure_score": 0,
            "checks": [],
            "total_weight": 0,
            "weight_breakdown": {}
        }
        
        try:
            # Check if network exists
            if not os.path.exists(network_path):
                result["checks"].append({
                    "name": "Network Path Validation",
                    "status": "FAIL",
                    "message": f"Network path does not exist: {network_path}",
                    "weight": 10,
                    "impact": "critical"
                })
                return result
            
            # Check for .tdn file if available
            tdn_files = list(Path(network_path).glob("*.tdn"))
            if tdn_files:
                result["checks"].append({
                    "name": "TDN File Export",
                    "status": "PASS",
                    "message": f"Found {len(tdn_files)} TDN export file(s)",
                    "weight": 10,
                    "impact": "high"
                })
                result["structure_score"] += 10
            else:
                # Look for .py files
                py_files = list(Path(network_path).glob("*.py"))
                if py_files:
                    result["checks"].append({
                        "name": "Python Script Documentation",
                        "status": "PASS",
                        "message": f"Found {len(py_files)} Python documentation files",
                        "weight": 8,
                        "impact": "medium"
                    })
                    result["structure_score"] += 8
                else:
                    result["checks"].append({
                        "name": "Documentation Presence",
                        "status": "WARN",
                        "message": "No documentation exports found (.tdn or .py files)",
                        "weight": 10,
                        "impact": "high"
                    })
                    
            # Check for essential components
            essential_files = ["__init__.py", "index.py"]
            existing_essential = []
            for essential in essential_files:
                if (Path(network_path) / essential).exists():
                    existing_essential.append(essential)
                    
            if existing_essential:
                result["checks"].append({
                    "name": "Essential Components",
                    "status": "PASS",
                    "message": f"Found essential components: {', '.join(existing_essential)}",
                    "weight": 15,
                    "impact": "high"
                })
                result["structure_score"] += 15
            else:
                result["checks"].append({
                    "name": "Essential Components",
                    "status": "WARN",
                    "message": "No essential components found (__init__.py, index.py)",
                    "weight": 15,
                    "impact": "medium"
                })
                
            # Check for README
            readme_files = list(Path(network_path).glob("README.md")) + \
                         list(Path(network_path).glob("readme.md")) + \
                         list(Path(network_path).glob("README.txt"))
            if readme_files:
                result["checks"].append({
                    "name": "Documentation",
                    "status": "PASS",
                    "message": f"Found {len(readme_files)} README/documentation file(s)",
                    "weight": 5,
                    "impact": "low"
                })
                result["structure_score"] += 5
                
        except Exception as e:
            result["checks"].append({
                "name": "Network Validation",
                "status": "ERROR",
                "message": f"Error validating network: {str(e)}",
                "weight": 10,
                "impact": "critical"
            })
            
        return result

    def validate_render_completeness(self, network_name: str) -> Dict[str, Any]:
        """Validate that renders and outputs exist."""
        print(f"Validating render completeness: {network_name}")
        
        result = {
            "completeness_score": 0,
            "missing_assets": [],
            "checks": [],
            "total_weight": 0,
            "weight_breakdown": {}
        }
        
        # Check for expected render directories
        render_dirs = ["renders", "screenshots", "outputs", "exports"]
        found_renders = []
        
        for render_dir in render_dirs:
            render_path = Path(f"genviromentPortfolio") / "BS_GodFile" / "my-site-clean" / "wix" / "renders"
            if render_path.exists():
                found_renders.append(render_dir)
                
        if found_renders:
            result["checks"].append({
                "name": "Render Directory Structure",
                "status": "PASS",
                "message": f"Found render directories: {', '.join(found_renders)}",
                "weight": 20,
                "impact": "high"
            })
            result["completeness_score"] += 20
        else:
            result["checks"].append({
                "name": "Render Directory Structure",
                "status": "FAIL",
                "message": "No expected render directories found (renders, screenshots, outputs, exports)",
                "weight": 20,
                "impact": "high"
            })
            
        # Check for TouchDesigner generated assets
        td_patterns = [
            "*.jpg", "*.png", "*.jpeg", "*.webp", "*.mp4",
            "*.json", "*.xml", "*.dat",
            "*meta.json", "*manifest.json"
        ]
        
        all_assets = []
        for pattern in td_patterns:
            pattern_path = Path(f"EnvironmentPortfolio") / "BS_GodFile" / "my-site-clean" / "wix" / "**" / pattern
            assets = list(Path(PROJECT_ROOT).rglob(pattern))
            all_assets.extend(assets)
            
        if all_assets:
            result["checks"].append({
                "name": "Asset Generation",
                "status": "PASS",
                "message": f"Found {len(all_assets)} TouchDesigner-generated asset(s)",
                "weight": 15,
                "impact": "high"
            })
            result["completeness_score"] += 15
            
            # Sample some asset info for report
            image_assets = [a for a in all_assets if str(a).lower().endswith(('.jpg', '.png', '.jpeg', '.webp'))]
            json_assets = [a for a in all_assets if str(a).lower().endswith('.json')]
            
            if image_assets:
                result["checks"].append({
                    "name": "Image Assets",
                    "status": "INFO",
                    "message": f"Found {len(image_assets)} image assets (renders/screenshots)",
                    "weight": 5,
                    "impact": "low"
                })
            if json_assets:
                result["checks"].append({
                    "name": "JSON Assets",
                    "status": "INFO",
                    "message": f"Found {len(json_assets)} JSON asset manifests",
                    "weight": 3,
                    "impact": "low"
                })
        else:
            result["checks"].append({
                "name": "Asset Generation",
                "status": "FAIL",
                "message": "No TouchDesigner-generated assets found",
                "weight": 15,
                "impact": "high"
            })
            
        return result

    def validate_performance_optimization(self) -> Dict[str, Any]:
        """Validate performance optimization best practices."""
        print("Validating performance optimization...")
        
        result = {
            "performance_score": 0,
            "optimization_checks": [],
            "checks": [],
            "total_weight": 0,
            "weight_breakdown": {}
        }
        
        # Check for optimization analysis files
        optimization_files = [
            "*optimization.json",
            "*performance.json",
            "*analysis.json",
            "*metrics.json"
        ]
        
        found_optimization = False
        for pattern in optimization_files:
            files = list(Path(PROJECT_ROOT).rglob(pattern))
            if files:
                found_optimization = True
                result["checks"].append({
                    "name": "Performance Analysis",
                    "status": "PASS",
                    "message": f"Found optimization files: {[f.name for f in files]}",
                    "weight": 10,
                    "impact": "medium"
                })
                result["performance_score"] += 10
                break
                
        if not found_optimization:
            # Check for performance-related hints in other files
            hints_dir = Path(PROJECT_ROOT) / "BS_GodFile" / "deploy" / "surreal_world"
            if hints_dir.exists():
                hint_files = list(hints_dir.glob("*quality*")) + \
                           list(hints_dir.glob("*optimization*")) + \
                           list(hints_dir.glob("*performance*"))
                if hint_files:
                    result["checks"].append({
                        "name": "Performance Analysis",
                        "status": "INFO",
                        "message": f"Found {len(hint_files)} optimization-related files in deploy/surreal_world/",
                        "weight": 5,
                        "impact": "low"
                    })
                    result["performance_score"] += 5
                else:
                    result["checks"].append({
                        "name": "Performance Analysis",
                        "status": "WARN",
                        "message": "No optimization analysis files found",
                        "weight": 10,
                        "impact": "medium"
                    })
            else:
                result["checks"].append({
                    "name": "Performance Analysis",
                    "status": "WARN",
                    "message": "No optimization analysis infrastructure found",
                    "weight": 10,
                    "impact": "medium"
                })
                
        return result

    def validate_web_integration(self) -> Dict[str, Any]:
        """Validate integration with web pipeline."""
        print("Validating web integration...")
        
        result = {
            "integration_score": 0,
            "checks": [],
            "total_weight": 0,
            "weight_breakdown": {}
        }
        
        # Check for web pipeline files
        web_pipeline_files = [
            "deploy/generate_web_manifest.py",
            "deploy/ai_tool_router.py",
            "deploy/surreal_world/export.py",
            "deploy/surreal_os/atoms.py"
        ]
        
        found_web_files = []
        for file in web_pipeline_files:
            if os.path.exists(Path(PROJECT_ROOT) / file):
                found_web_files.append(file)
                
        if found_web_files:
            result["checks"].append({
                "name": "Web Integration Infrastructure",
                "status": "PASS",
                "message": f"Found {len(found_web_files)} web integration files",
                "weight": 20,
                "impact": "high"
            })
            result["integration_score"] += 20
        else:
            result["checks"].append({
                "name": "Web Integration Infrastructure",
                "status": "FAIL",
                "message": "Critical web integration files missing",
                "weight": 20,
                "impact": "critical"
            })
            
        # Check for web deployment configuration
        web_configs = [
            "BS_GodFile/my-site-clean/package.json",
            "BS_GodFile/my-site-clean/wix.config.json",
            "BS_GodFile/my-site-clean/wix/index.html"
        ]
        
        if all(os.path.exists(Path(PROJECT_ROOT) / file) for file in web_configs):
            result["checks"].append({
                "name": "Web Deployment Configuration",
                "status": "PASS",
                "message": "All required web deployment configuration files found",
                "weight": 15,
                "impact": "high"
            })
            result["integration_score"] += 15
        else:
            result["checks"].append({
                "name": "Web Deployment Configuration",
                "status": "FAIL",
                "message": "Missing required web configuration files",
                "weight": 15,
                "impact": "critical"
            })
            
        return result

    def validate_mcp_integration(self) -> Dict[str, Any]:
        """Validate MCP server integration."""
        print("Validating MCP integration...")
        
        result = {
            "mcp_score": 0,
            "checks": [],
            "total_weight": 0,
            "weight_breakdown": {}
        }
        
        # Check for MCP-related infrastructure
        mcp_infrastructure = [
            "deploy/agent_bridge_mcp.py",
            "deploy/blender_mcp_adapter.py",
            "deploy/surreal_arch_mcp_adapter.py"
        ]
        
        found_mcp = []
        for file in mcp_infrastructure:
            if os.path.exists(Path(PROJECT_ROOT) / file):
                found_mcp.append(file)
                
        if found_mcp:
            result["checks"].append({
                "name": "MCP Infrastructure",
                "status": "PASS",
                "message": f"Found {len(found_mcp)} MCP integration files",
                "weight": 15,
                "impact": "high"
            })
            result["mcp_score"] += 15
        else:
            result["checks"].append({
                "name": "MCP Infrastructure",
                "status": "FAIL",
                "message": "No MCP integration infrastructure found",
                "weight": 15,
                "impact": "high"
            })
            
        # Check for TouchDesigner MCP protocols
        mcp_protocols = [
            "Runtime/TouchDesigner/Envoy/ext/EnvoyExt.py",
            "touchdesigner-interop-research.md"
        ]
        
        found_protocols = []
        for file in mcp_protocols:
            if os.path.exists(Path(PROJECT_ROOT) / file):
                found_protocols.append(file)
                
        if found_protocols:
            result["checks"].append({
                "name": "MCP Protocols",
                "status": "PASS",
                "message": f"Found {len(found_protocols)} MCP protocol definitions",
                "weight": 10,
                "impact": "medium"
            })
            result["mcp_score"] += 10
        else:
            result["checks"].append({
                "name": "MCP Protocols",
                "status": "WARN",
                "message": "No MCP protocol definitions found",
                "weight": 10,
                "impact": "medium"
            })
            
        return result

    def generate_report(self, validation_results: Dict[str, Any]) -> Dict[str, Any]:
        """Generate comprehensive validation report."""
        print("Generating validation report...")
        
        # Score calculation with weighting
        weights = {
            "structure": 25,
            "completeness": 30,
            "performance": 20,
            "integration": 25,
            "mcp": 20
        }
        
        scores = validation_results.get("scores", {})
        overall_score = 0
        total_weight = sum(weights.values())
        
        for category, weight in weights.items():
            score = scores.get(f"{category}_score", 0)
            overall_score += score * (weight / 100)
        
        report = {
            "validation_report": {
                "timestamp": datetime.now().isoformat(),
                "overall_score": round(overall_score, 1),
                "assessment": self._get_assessment(overall_score),
                "categories": {}
            }
        }
        
        # Populate category reports
        for category in weights.keys():
            category_score = scores.get(f"{category}_score", 0)
            category_checks = validation_results.get(f"{category}_checks", [])
            
            report["validation_report"]["categories"][category] = {
                "score": category_score,
                "weight": weights[category],
                "weight_contribution": round(category_score * (weights[category] / 100), 1),
                "status": self._get_category_status(category_score),
                "recommendations": self._generate_category_recommendations(category, category_score)
            }
            
        # Add findings and recommendations
        report["validation_report"]["findings"] = validation_results.get("findings", [])
        report["validation_report"]["recommendations"] = validation_results.get("recommendations", [])
        report["validation_report"]["raw_checks"] = validation_results.get("all_checks", [])
        
        return report

    def _get_assessment(self, score: float) -> str:
        """Get overall assessment based on score."""
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

    def _get_category_status(self, score: float) -> str:
        """Get category status based on score."""
        if score >= 90:
            return "PASS"
        elif score >= 80:
            return "NEAR_PASS"
        elif score >= 70:
            return "MARGINAL"
        elif score >= 60:
            return "NEEDS_IMPROVEMENT"
        elif score >= 50:
            return "CONCERNING"
        else:
            return "CRITICAL"

    def _generate_category_recommendations(self, category: str, score: float) -> List[str]:
        """Generate recommendations for a category."""
        recommendations = []
        
        if score < 70:
            if category == "structure":
                recommendations.extend([
                    "Add TDN or .py documentation exports",
                    "Create essential component files (__init__.py, index.py)",
                    "Add comprehensive README documentation"
                ])
            elif category == "completeness":
                recommendations.extend([
                    "Set up render directories (renders/, screenshots/, outputs/)",
                    "Generate TouchDesigner assets (images, JSON manifests)",
                    "Implement checkpoint system for render outputs"
                ])
            elif category == "performance":
                recommendations.extend([
                    "Add performance analysis files",
                    "Implement optimization metrics tracking",
                    "Add benchmark reports and comparisons"
                ])
            elif category == "integration":
                recommendations.extend([
                    "Implement web pipeline integration",
                    "Add deployment configuration files",
                    "Create webhook integrations"
                ])
            elif category == "mcp":
                recommendations.extend([
                    "Implement TouchDesigner MCP adapter",
                    "Add server communication protocols",
                    "Create API endpoint documentation"
                ])
                
        return recommendations

    def run_comprehensive_validation(self, network_path: Optional[str] = None) -> Dict[str, Any]:
        """Run comprehensive validation of TouchDesigner integration."""
        print("=" * 60)
        print("TOUCHDESIGNER VALIDATION SYSTEM")
        print("=" * 60)
        
        validation_results = {
            "timestamp": datetime.now().isoformat(),
            "all_checks": [],
            "findings": [],
            "recommendations": [],
            "scores": {}
        }
        
        # Run all validation checks
        if network_path and os.path.exists(network_path):
            validation_results["network_structure"] = self.validate_network_structure(network_path)
            validation_results["all_checks"].extend(validation_results["network_structure"].get("checks", []))
            validation_results["findings"].extend(self._extract_findings(validation_results["network_structure"]))
            validation_results["recommendations"].extend(self._extract_recommendations(validation_results["network_structure"]))
            
        validation_results["render_completeness"] = self.validate_render_completeness("TouchDesigner")
        validation_results["all_checks"].extend(validation_results["render_completeness"].get("checks", []))
        validation_results["findings"].extend(self._extract_findings(validation_results["render_completeness"]))
        validation_results["recommendations"].extend(self._extract_recommendations(validation_results["render_completeness"]))
        
        validation_results["performance"] = self.validate_performance_optimization()
        validation_results["all_checks"].extend(validation_results["performance"].get("checks", []))
        validation_results["findings"].extend(self._extract_findings(validation_results["performance"]))
        validation_results["recommendations"].extend(self._extract_recommendations(validation_results["performance"]))
        
        validation_results["integration"] = self.validate_web_integration()
        validation_results["all_checks"].extend(validation_results["integration"].get("checks", []))
        validation_results["findings"].extend(self._extract_findings(validation_results["integration"]))
        validation_results["recommendations"].extend(self._extract_recommendations(validation_results["integration"]))
        
        validation_results["mcp"] = self.validate_mcp_integration()
        validation_results["all_checks"].extend(validation_results["mcp"].get("checks", []))
        validation_results["findings"].extend(self._extract_findings(validation_results["mcp"]))
        validation_results["recommendations"].extend(self._extract_recommendations(validation_results["mcp"]))
        
        # Calculate scores
        validation_results["scores"] = {
            "structure_score": validation_results.get("network_structure", {}).get("structure_score", 0),
            "completeness_score": validation_results.get("render_completeness", {}).get("completeness_score", 0),
            "performance_score": validation_results.get("performance", {}).get("performance_score", 0),
            "integration_score": validation_results.get("integration", {}).get("integration_score", 0),
            "mcp_score": validation_results.get("mcp", {}).get("mcp_score", 0)
        }
        
        # Generate report
        validation_results["validation_report"] = self.generate_report(validation_results)
        
        return validation_results

    def _extract_findings(self, validation_result: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract findings from validation result."""
        findings = []
        
        for check in validation_result.get("checks", []):
            if check.get("status") in ["FAIL", "ERROR", "WARN"]:
                findings.append({
                    "category": check.get("name", "Unknown"),
                    "severity": self._get_severity_from_status(check.get("status", ""), check.get("impact", "")),
                    "message": check.get("message", ""),
                    "weight": check.get("weight", 0),
                    "impact": check.get("impact", "")
                })
                
        return findings

    def _extract_recommendations(self, validation_result: Dict[str, Any]) -> List[str]:
        """Extract recommendations from validation result."""
        recommendations = []
        
        for check in validation_result.get("checks", []):
            if check.get("impact") in ["critical", "high"] and check.get("status") in ["FAIL", "ERROR", "WARN"]:
                recommendations.append(f"{check.get('name')}: {check.get('message')}")
                
        return recommendations

    def _get_severity_from_status(self, status: str, impact: str) -> str:
        """Get severity from status and impact."""
        if impact == "critical":
            return "CRITICAL"
        elif status == "ERROR":
            return "ERROR"
        elif impact == "high":
            return "HIGH"
        elif status == "FAIL":
            return "MEDIUM"
        elif status == "WARN":
            return "LOW"
        else:
            return "INFO"


def save_report(report: Dict[str, Any], output_path: str) -> None:
    """Save validation report to file."""
    try:
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        print(f"Report saved to: {output_path}")
    except Exception as e:
        print(f"Error saving report: {str(e)}")


def main():
    parser = argparse.ArgumentParser(
        description="TouchDesigner Validation and Review System"
    )
    
    parser.add_argument(
        "--validate",
        help="Path to TouchDesigner network to validate"
    )
    
    parser.add_argument(
        "--validate-all",
        action="store_true",
        help="Run comprehensive validation on entire project"
    )
    
    parser.add_argument(
        "--review",
        help="Path to TouchDesigner network for review (includes manual assessment)"
    )
    
    parser.add_argument(
        "--output",
        default="C:/EnvironmentPortfolio/BS_GodFile/Saved/Audit/touchdesigner_validation_report.json",
        help="Output path for validation report (default: BS_GodFile/Saved/Audit/)"
    )
    
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Minimal output (no progress messages)"
    )
    
    args = parser.parse_args()
    
    validator = TouchDesignerValidator()
    
    validation_results = {}
    
    if args.validate:
        if not args.quiet:
            print(f"Validating network: {args.validate}")
        validation_results = validator.run_comprehensive_validation(args.validate)
    elif args.validate_all:
        if not args.quiet:
            print("Running comprehensive validation on entire project...")
        validation_results = validator.run_comprehensive_validation()
    elif args.review:
        if not args.quiet:
            print(f"Reviewing network: {args.review}")
        validation_results = validator.run_comprehensive_validation(args.review)
    else:
        parser.print_help()
        return
        
    # Save report
    if not args.quiet:
        print(f"\nValidation completed. Generating report...")
    
    save_report(validation_results, args.output)
    
    # Display summary
    if not args.quiet:
        score = validation_results.get("validation_report", {}).get("overall_score", 0)
        assessment = validation_results.get("validation_report", {}).get("assessment", "UNKNOWN")
        print(f"\nVALIDATION SUMMARY:")
        print(f"  Overall Score: {score}/100")
        print(f"  Assessment: {assessment}")
        print(f"  Report saved to: {args.output}")
        
        # Show critical findings
        critical = [f for f in validation_results.get("findings", []) if f.get("severity") == "CRITICAL"]
        if critical:
            print(f"\nCRITICAL ISSUES FOUND ({len(critical)}):")
            for finding in critical[:5]:  # Show first 5
                print(f"  *️  {finding.get('category')}: {finding.get('message')}")


if __name__ == "__main__":
    main()
