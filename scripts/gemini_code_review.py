#!/usr/bin/env python3
"""
Gemini AI Code Review Script
Analyzes code changes for security, performance, and best practice issues
"""

import json
import os
import sys
import argparse
import subprocess
from pathlib import Path
from datetime import datetime

try:
    import google.generativeai as genai
except ImportError:
    print("❌ Error: google-generativeai not installed")
    print("Install with: pip install google-generativeai")
    sys.exit(1)


class GeminiCodeReviewer:
    """Reviews code changes using Google Gemini AI"""
    
    def __init__(self, api_key: str):
        """Initialize Gemini client"""
        self.api_key = api_key
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-pro')
        self.safety_settings = [
            {
                "category": "HARM_CATEGORY_HARASSMENT",
                "threshold": "BLOCK_NONE",
            },
            {
                "category": "HARM_CATEGORY_HATE_SPEECH",
                "threshold": "BLOCK_NONE",
            },
            {
                "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
                "threshold": "BLOCK_NONE",
            },
            {
                "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
                "threshold": "BLOCK_NONE",
            },
        ]
    
    def get_file_content(self, file_path: str) -> str:
        """Read file content"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            print(f"⚠️  Could not read {file_path}: {e}")
            return ""
    
    def get_git_diff(self) -> str:
        """Get git diff for changed files"""
        try:
            result = subprocess.run(
                ['git', 'diff', 'HEAD~1', 'HEAD'],
                capture_output=True,
                text=True,
                timeout=30
            )
            return result.stdout[:5000]  # Limit to first 5000 chars
        except Exception as e:
            print(f"⚠️  Could not get git diff: {e}")
            return ""
    
    def analyze_code(self, changed_files: list, analysis_type: str = "general") -> dict:
        """Analyze code changes with Gemini"""
        
        file_contents = ""
        for file_path in changed_files[:10]:  # Limit to 10 files
            content = self.get_file_content(file_path)
            if content:
                file_contents += f"\n\n=== {file_path} ===\n{content[:2000]}"  # Limit each file
        
        if not file_contents:
            git_diff = self.get_git_diff()
            if git_diff:
                file_contents = f"\n\n=== Git Diff ===\n{git_diff}"
        
        if analysis_type == "security":
            prompt = self._create_security_prompt(file_contents)
        elif analysis_type == "performance":
            prompt = self._create_performance_prompt(file_contents)
        elif analysis_type == "kubernetes":
            prompt = self._create_kubernetes_prompt(file_contents)
        else:
            prompt = self._create_general_prompt(file_contents)
        
        try:
            response = self.model.generate_content(
                prompt,
                safety_settings=self.safety_settings,
                generation_config=genai.types.GenerationConfig(
                    temperature=0.3,
                    top_p=0.95,
                    top_k=40,
                    max_output_tokens=2048,
                )
            )
            return {
                "status": "success",
                "analysis": response.text,
                "type": analysis_type
            }
        except Exception as e:
            print(f"❌ Error during AI analysis: {e}")
            return {
                "status": "error",
                "error": str(e),
                "type": analysis_type
            }
    
    def _create_general_prompt(self, content: str) -> str:
        return f"""
        You are an expert code reviewer. Analyze the following code changes for:
        
        1. **Security Issues**: Potential vulnerabilities, injection attacks, authentication issues
        2. **Performance Concerns**: Inefficient algorithms, N+1 queries, memory leaks
        3. **Best Practices**: Code style, error handling, logging, testing
        4. **Bug Risks**: Logic errors, edge cases, null pointer risks
        
        Code Changes:
        {content}
        
        Provide a structured review with:
        - **Issues Found**: List each issue with severity (CRITICAL/HIGH/MEDIUM/LOW)
        - **Recommendations**: Specific fixes for each issue
        - **Overall Assessment**: General impression and risk level
        
        Be constructive and specific. Reference exact lines if possible.
        """
    
    def _create_security_prompt(self, content: str) -> str:
        return f"""
        You are a security expert. Perform a SECURITY-FOCUSED code review of:
        
        {content}
        
        Check for:
        1. **Authentication/Authorization Issues**: JWT, OAuth, session management
        2. **SQL Injection/NoSQL Injection**: Parameter handling, query construction
        3. **XSS/CSRF**: Input validation, output encoding
        4. **Cryptography**: Weak encryption, hardcoded secrets, deprecated algorithms
        5. **Dependency Vulnerabilities**: Known vulnerable libraries
        6. **AWS/Cloud Security**: IAM policies, data exposure, encryption
        7. **Docker Security**: Image scanning, secrets in Dockerfile, privilege escalation
        
        For each issue found, provide severity level (CRITICAL/HIGH/MEDIUM/LOW) and remediation.
        """
    
    def _create_performance_prompt(self, content: str) -> str:
        return f"""
        You are a performance optimization expert. Analyze:
        
        {content}
        
        Check for:
        1. **Algorithm Efficiency**: O(n²) loops, inefficient sorting, unnecessary iterations
        2. **Database Queries**: N+1 problems, missing indexes, inefficient joins
        3. **Memory Management**: Memory leaks, unnecessary object creation
        4. **Resource Utilization**: CPU, memory, disk I/O optimization opportunities
        5. **Caching**: Missing cache opportunities, cache invalidation issues
        6. **Async/Concurrency**: Blocking operations, thread pool issues
        7. **Java Specifics**: String concatenation instead of StringBuilder, excessive GC pressure
        
        Provide metrics-aware recommendations with estimated improvement.
        """
    
    def _create_kubernetes_prompt(self, content: str) -> str:
        return f"""
        You are a Kubernetes configuration expert. Validate:
        
        {content}
        
        Check Kubernetes manifests (YAML) for:
        1. **Resource Management**: CPU/memory requests and limits
        2. **Health Checks**: Readiness probes, liveness probes, startup probes
        3. **Security**: Security context, network policies, RBAC
        4. **Best Practices**: Labels, annotations, namespace usage
        5. **High Availability**: Replica counts, pod disruption budgets
        6. **Monitoring**: Logging, metrics, tracing configuration
        7. **Deployment Strategy**: Rolling updates, canary deployments
        
        Provide specific fixes for each misconfiguration.
        """
    
    def generate_markdown_report(self, analyses: list) -> str:
        """Generate markdown report from analyses"""
        report = f"""# Code Review Report
Generated: {datetime.now().isoformat()}

## Summary
- Total Analyses: {len(analyses)}
- Passed: {sum(1 for a in analyses if a['status'] == 'success')}
- Failed: {sum(1 for a in analyses if a['status'] == 'error')}

## Detailed Analysis

"""
        
        for i, analysis in enumerate(analyses, 1):
            report += f"\n### {i}. {analysis['type'].upper()} Review\n"
            
            if analysis['status'] == 'success':
                report += f"{analysis['analysis']}\n"
            else:
                report += f"❌ **Error**: {analysis.get('error', 'Unknown error')}\n"
            
            report += "\n---\n"
        
        return report


def main():
    parser = argparse.ArgumentParser(
        description='Review code changes using Gemini AI',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument('--changed-files', type=str, default='',
                        help='Space-separated list of changed files')
    parser.add_argument('--api-key', type=str, required=True,
                        help='Gemini API key')
    parser.add_argument('--workflow-run-id', type=str, default='',
                        help='GitHub workflow run ID')
    parser.add_argument('--include-security', action='store_true',
                        help='Include security-focused review')
    parser.add_argument('--include-performance', action='store_true',
                        help='Include performance review')
    parser.add_argument('--include-kubernetes', action='store_true',
                        help='Include Kubernetes validation')
    
    args = parser.parse_args()
    
    # Parse changed files
    changed_files = [f.strip() for f in args.changed_files.split() if f.strip()]
    
    print(f"🔍 Starting Gemini AI Code Review")
    print(f"📝 Changed files: {len(changed_files)}")
    print(f"🔑 API Key configured: {bool(args.api_key)}")
    
    # Initialize reviewer
    reviewer = GeminiCodeReviewer(args.api_key)
    
    analyses = []
    
    # General review
    print("\n📋 Running general code review...")
    general_review = reviewer.analyze_code(changed_files, "general")
    analyses.append(general_review)
    if general_review['status'] == 'success':
        print("✅ General review completed")
    else:
        print(f"❌ General review failed: {general_review.get('error')}")
    
    # Security review (if requested or Docker/Kubernetes files changed)
    has_docker = any('docker' in f.lower() for f in changed_files)
    has_k8s = any('k8s' in f.lower() or 'yml' in f.lower() for f in changed_files)
    
    if args.include_security or has_docker:
        print("\n🔒 Running security review...")
        security_review = reviewer.analyze_code(changed_files, "security")
        analyses.append(security_review)
        if security_review['status'] == 'success':
            print("✅ Security review completed")
        else:
            print(f"❌ Security review failed: {security_review.get('error')}")
    
    # Performance review (if requested)
    if args.include_performance:
        print("\n⚡ Running performance review...")
        perf_review = reviewer.analyze_code(changed_files, "performance")
        analyses.append(perf_review)
        if perf_review['status'] == 'success':
            print("✅ Performance review completed")
        else:
            print(f"❌ Performance review failed: {perf_review.get('error')}")
    
    # Kubernetes review (if K8s files changed)
    if args.include_kubernetes or has_k8s:
        print("\n☸️  Running Kubernetes validation...")
        k8s_review = reviewer.analyze_code(changed_files, "kubernetes")
        analyses.append(k8s_review)
        if k8s_review['status'] == 'success':
            print("✅ Kubernetes validation completed")
        else:
            print(f"❌ Kubernetes validation failed: {k8s_review.get('error')}")
    
    # Generate report
    print("\n📄 Generating report...")
    report = reviewer.generate_markdown_report(analyses)
    
    # Save report
    with open('review_output.md', 'w') as f:
        f.write(report)
    
    # Save JSON for programmatic access
    with open('review_output.json', 'w') as f:
        json.dump(analyses, f, indent=2)
    
    # Print summary
    print("\n" + "="*60)
    print("REVIEW SUMMARY")
    print("="*60)
    
    success_count = sum(1 for a in analyses if a['status'] == 'success')
    error_count = sum(1 for a in analyses if a['status'] == 'error')
    
    print(f"✅ Successful analyses: {success_count}")
    print(f"❌ Failed analyses: {error_count}")
    print(f"\n📄 Report saved to: review_output.md")
    print(f"📊 JSON output saved to: review_output.json")
    
    # Set GitHub output variables
    if os.getenv('GITHUB_OUTPUT'):
        with open(os.getenv('GITHUB_OUTPUT'), 'a') as f:
            result = "PASSED" if error_count == 0 else "FAILED"
            f.write(f"result={result}\n")
            f.write(f"security-issues={sum(1 for a in analyses if 'security' in a.get('type', ''))}\n")
            f.write(f"performance-concerns={sum(1 for a in analyses if 'performance' in a.get('type', ''))}\n")
    
    # Exit with appropriate code
    sys.exit(0 if error_count == 0 else 1)


if __name__ == '__main__':
    main()
