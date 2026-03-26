#!/usr/bin/env python3
"""
Gemini AI Deployment Validation Script
Validates Kubernetes deployment health and Gemini AI checks
"""

import json
import os
import sys
import argparse
import subprocess
import time
from datetime import datetime
from typing import List, Dict, Any

try:
    import google.generativeai as genai
except ImportError:
    print("❌ Error: google-generativeai not installed")
    sys.exit(1)


class KubernetesValidator:
    """Validates Kubernetes deployment using kubectl and Gemini AI"""
    
    def __init__(self, api_key: str, namespace: str):
        self.api_key = api_key
        self.namespace = namespace
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-pro')
        self.validation_results = {}
    
    def run_kubectl(self, command: str) -> tuple:
        """Execute kubectl command"""
        try:
            result = subprocess.run(
                command.split(),
                capture_output=True,
                text=True,
                timeout=30
            )
            return result.returncode, result.stdout, result.stderr
        except subprocess.TimeoutExpired:
            return 1, "", "Command timeout"
        except Exception as e:
            return 1, "", str(e)
    
    def check_pods_running(self, deployment: str) -> Dict[str, Any]:
        """Check if pods are running and healthy"""
        print(f"🔍 Checking pods for deployment: {deployment}")
        
        # Get pods
        cmd = f"kubectl get pods -n {self.namespace} -l app={deployment.split('-')[0]} -o json"
        returncode, stdout, stderr = self.run_kubectl(cmd)
        
        if returncode != 0:
            return {
                "status": "error",
                "message": f"Failed to get pods: {stderr}",
                "pods_running": 0
            }
        
        try:
            pods_data = json.loads(stdout)
            pods = pods_data.get('items', [])
            
            running_pods = []
            ready_pods = []
            unhealthy_pods = []
            
            for pod in pods:
                pod_name = pod['metadata']['name']
                pod_status = pod['status']['phase']
                
                if pod_status == 'Running':
                    running_pods.append(pod_name)
                    
                    # Check if ready
                    conditions = pod['status'].get('conditions', [])
                    is_ready = any(c['type'] == 'Ready' and c['status'] == 'True' 
                                  for c in conditions)
                    if is_ready:
                        ready_pods.append(pod_name)
                    else:
                        unhealthy_pods.append((pod_name, 'Not Ready'))
                elif pod_status != 'Succeeded':
                    unhealthy_pods.append((pod_name, pod_status))
            
            result = {
                "status": "success",
                "total_pods": len(pods),
                "running_pods": len(running_pods),
                "ready_pods": len(ready_pods),
                "unhealthy_pods": len(unhealthy_pods),
                "pods": {
                    "running": running_pods,
                    "ready": ready_pods,
                    "unhealthy": unhealthy_pods
                }
            }
            
            print(f"✅ Pods: Total={len(pods)}, Running={len(running_pods)}, Ready={len(ready_pods)}")
            
            return result
        except json.JSONDecodeError as e:
            return {
                "status": "error",
                "message": f"Failed to parse pods JSON: {e}",
                "pods_running": 0
            }
    
    def check_service_status(self) -> Dict[str, Any]:
        """Check service status and LoadBalancer"""
        print("🔍 Checking service status...")
        
        cmd = f"kubectl get svc currency-conversion-service -n {self.namespace} -o json"
        returncode, stdout, stderr = self.run_kubectl(cmd)
        
        if returncode != 0:
            return {
                "status": "error",
                "message": f"Failed to get service: {stderr}"
            }
        
        try:
            svc_data = json.loads(stdout)
            svc_type = svc_data['spec']['type']
            ports = svc_data['spec']['ports']
            
            # Check LoadBalancer
            lb_info = svc_data['status'].get('loadBalancer', {})
            ingress = lb_info.get('ingress', [])
            
            lb_ip = None
            lb_hostname = None
            if ingress:
                lb_ip = ingress[0].get('ip')
                lb_hostname = ingress[0].get('hostname')
            
            result = {
                "status": "success",
                "service_type": svc_type,
                "ports": [f"{p.get('port')}/{p.get('targetPort')}" for p in ports],
                "loadbalancer": {
                    "ip": lb_ip,
                    "hostname": lb_hostname,
                    "ready": bool(lb_ip or lb_hostname)
                }
            }
            
            if not result['loadbalancer']['ready']:
                print("⏳ LoadBalancer IP pending (normal for AWS ELB, wait 2-5 minutes)")
            else:
                print(f"✅ LoadBalancer ready at: {lb_ip or lb_hostname}")
            
            return result
        except json.JSONDecodeError as e:
            return {
                "status": "error",
                "message": f"Failed to parse service JSON: {e}"
            }
    
    def check_pod_logs(self, deployment: str) -> Dict[str, Any]:
        """Check pod logs for errors"""
        print("🔍 Checking pod logs...")
        
        cmd = f"kubectl logs -n {self.namespace} -l app={deployment.split('-')[0]} --tail=50 --timestamps=true"
        returncode, stdout, stderr = self.run_kubectl(cmd)
        
        # Parse logs
        error_count = stdout.lower().count('error')
        exception_count = stdout.lower().count('exception')
        warn_count = stdout.lower().count('warn')
        
        recent_logs = stdout.split('\n')[-20:]  # Last 20 lines
        
        return {
            "status": "success",
            "error_count": error_count,
            "exception_count": exception_count,
            "warning_count": warn_count,
            "recent_logs": recent_logs,
            "has_critical_errors": error_count > 0 or exception_count > 0
        }
    
    def check_resource_usage(self) -> Dict[str, Any]:
        """Check pod resource usage"""
        print("🔍 Checking resource usage...")
        
        cmd = f"kubectl top pods -n {self.namespace}"
        returncode, stdout, stderr = self.run_kubectl(cmd)
        
        if returncode != 0:
            # Metrics might not be available yet
            return {
                "status": "unavailable",
                "message": "Metrics server not available yet (normal)"
            }
        
        # Parse metrics
        lines = stdout.strip().split('\n')[1:]  # Skip header
        pods_metrics = []
        
        for line in lines:
            if not line.strip():
                continue
            parts = line.split()
            if len(parts) >= 3:
                pods_metrics.append({
                    "pod": parts[0],
                    "cpu": parts[1],
                    "memory": parts[2]
                })
        
        print(f"✅ Resource metrics: {len(pods_metrics)} pods measured")
        
        return {
            "status": "success",
            "pods_metrics": pods_metrics
        }
    
    def check_hpa_status(self) -> Dict[str, Any]:
        """Check HPA status and metrics"""
        print("🔍 Checking HPA status...")
        
        cmd = f"kubectl get hpa -n {self.namespace} -o json"
        returncode, stdout, stderr = self.run_kubectl(cmd)
        
        if returncode != 0:
            return {
                "status": "not_found",
                "message": "HPA not found"
            }
        
        try:
            hpa_data = json.loads(stdout)
            hpas = hpa_data.get('items', [])
            
            hpa_status = []
            for hpa in hpas:
                status = hpa['status']
                spec = hpa['spec']
                
                hpa_status.append({
                    "name": hpa['metadata']['name'],
                    "desired_replicas": status.get('desiredReplicas'),
                    "current_replicas": status.get('currentReplicas'),
                    "min_replicas": spec.get('minReplicas'),
                    "max_replicas": spec.get('maxReplicas'),
                    "current_cpu_utilization": status.get('currentCPUUtilizationPercentage'),
                    "target_cpu_utilization": spec.get('targetCPUUtilizationPercentage')
                })
            
            print(f"✅ HPA configured: {len(hpas)} autoscalers")
            
            return {
                "status": "success",
                "hpas": hpa_status
            }
        except json.JSONDecodeError as e:
            return {
                "status": "error",
                "message": f"Failed to parse HPA JSON: {e}"
            }
    
    def validate_with_gemini(self, validation_data: Dict[str, Any], 
                            deployment: str, image_uri: str) -> Dict[str, Any]:
        """Validate deployment with Gemini AI"""
        print("🤖 Running Gemini AI validation...")
        
        prompt = f"""
        You are a Kubernetes deployment expert. Analyze the deployment status and provide validation:
        
        **Deployment Context:**
        - Service: {deployment}
        - Image: {image_uri}
        - Namespace: {self.namespace}
        
        **Current Status:**
        {json.dumps(validation_data, indent=2)}
        
        Please provide:
        1. **Overall Health Assessment**: Green/Yellow/Red status with explanation
        2. **Issues Found**: Any problems or misconfigurations
        3. **Recommendations**: Specific actions to improve reliability
        4. **Risk Assessment**: Is this safe for production traffic?
        5. **Next Steps**: What to monitor or do next
        
        Be concise and actionable.
        """
        
        try:
            response = self.model.generate_content(
                prompt,
                safety_settings=[
                    {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
                    {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
                    {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
                    {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
                ],
                generation_config=genai.types.GenerationConfig(
                    temperature=0.3,
                    max_output_tokens=1024,
                )
            )
            
            return {
                "status": "success",
                "analysis": response.text
            }
        except Exception as e:
            print(f"⚠️  Gemini validation failed: {e}")
            return {
                "status": "error",
                "error": str(e)
            }
    
    def run_full_validation(self, deployment: str, image_uri: str) -> Dict[str, Any]:
        """Run complete deployment validation"""
        print("\n" + "="*60)
        print("KUBERNETES DEPLOYMENT VALIDATION")
        print("="*60 + "\n")
        
        validation_data = {}
        
        # Check pods
        validation_data['pods'] = self.check_pods_running(deployment)
        
        # Check service
        validation_data['service'] = self.check_service_status()
        
        # Check logs
        validation_data['logs'] = self.check_pod_logs(deployment)
        
        # Check resources
        validation_data['resources'] = self.check_resource_usage()
        
        # Check HPA
        validation_data['hpa'] = self.check_hpa_status()
        
        # Gemini AI validation
        print()
        gemini_validation = self.validate_with_gemini(validation_data, deployment, image_uri)
        validation_data['gemini_analysis'] = gemini_validation
        
        return validation_data
    
    def generate_report(self, validation_data: Dict[str, Any]) -> str:
        """Generate validation report"""
        report = f"""# Kubernetes Deployment Validation Report

**Generated**: {datetime.now().isoformat()}
**Namespace**: {self.namespace}

## Summary

"""
        
        # Pods status
        pods_info = validation_data.get('pods', {})
        if pods_info.get('status') == 'success':
            report += f"""### Pod Status ✅
- Total Pods: {pods_info.get('total_pods')}
- Running: {pods_info.get('running_pods')}
- Ready: {pods_info.get('ready_pods')}
- Unhealthy: {pods_info.get('unhealthy_pods')}

"""
        
        # Service status
        svc_info = validation_data.get('service', {})
        if svc_info.get('status') == 'success':
            lb_ready = svc_info.get('loadbalancer', {}).get('ready', False)
            report += f"""### Service Status
- Type: {svc_info.get('service_type')}
- Ports: {', '.join(svc_info.get('ports', []))}
- LoadBalancer Ready: {'✅ Yes' if lb_ready else '⏳ Pending'}
"""
            if svc_info.get('loadbalancer', {}).get('hostname'):
                report += f"- Address: {svc_info['loadbalancer']['hostname']}\n"
            report += "\n"
        
        # Logs status
        logs_info = validation_data.get('logs', {})
        if logs_info.get('status') == 'success':
            report += f"""### Application Logs
- Errors: {logs_info.get('error_count')}
- Exceptions: {logs_info.get('exception_count')}
- Warnings: {logs_info.get('warning_count')}
- Critical Issues: {'❌ Yes' if logs_info.get('has_critical_errors') else '✅ No'}

"""
        
        # HPA status
        hpa_info = validation_data.get('hpa', {})
        if hpa_info.get('status') == 'success':
            report += f"""### Auto-Scaling (HPA)
"""
            for hpa in hpa_info.get('hpas', []):
                report += f"""- {hpa['name']}: {hpa.get('current_replicas', '?')}/{hpa.get('desired_replicas', '?')} replicas
  (Min: {hpa.get('min_replicas')}, Max: {hpa.get('max_replicas')})

"""
        
        # Gemini analysis
        gemini_info = validation_data.get('gemini_analysis', {})
        if gemini_info.get('status') == 'success':
            report += f"""## Gemini AI Analysis

{gemini_info.get('analysis', 'No analysis available')}

"""
        
        return report


def main():
    parser = argparse.ArgumentParser(
        description='Validate Kubernetes deployment with Gemini AI'
    )
    parser.add_argument('--api-key', type=str, required=True,
                        help='Gemini API key')
    parser.add_argument('--namespace', type=str, default='production',
                        help='Kubernetes namespace')
    parser.add_argument('--deployment', type=str, default='currency-conversion-service',
                        help='Deployment name')
    parser.add_argument('--image-uri', type=str, default='',
                        help='Docker image URI')
    
    args = parser.parse_args()
    
    try:
        validator = KubernetesValidator(args.api_key, args.namespace)
        validation_data = validator.run_full_validation(args.deployment, args.image_uri)
        
        # Generate report
        report = validator.generate_report(validation_data)
        
        # Save report
        with open('validation_report.md', 'w') as f:
            f.write(report)
        
        # Save JSON
        with open('validation_data.json', 'w') as f:
            json.dump(validation_data, f, indent=2, default=str)
        
        print("\n" + "="*60)
        print("VALIDATION COMPLETE")
        print("="*60)
        print(f"\n📄 Report saved to: validation_report.md")
        print(f"📊 JSON data saved to: validation_data.json")
        
        # Determine exit code
        pods_info = validation_data.get('pods', {})
        has_critical_errors = validation_data.get('logs', {}).get('has_critical_errors', False)
        
        exit_code = 0
        if pods_info.get('status') != 'success' or pods_info.get('ready_pods', 0) < 2:
            print("\n⚠️  Deployment not fully ready")
            exit_code = 1
        elif has_critical_errors:
            print("\n⚠️  Critical errors detected in logs")
            exit_code = 1
        else:
            print("\n✅ Deployment validation passed!")
        
        sys.exit(exit_code)
    
    except Exception as e:
        print(f"\n❌ Validation failed: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
