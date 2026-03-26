# Gemini AI Integration Guide

## Overview

This project uses Google's Gemini AI to automate code reviews and deployment validation. Gemini AI performs intelligent analysis of:

1. **Code Security**: Vulnerabilities, injection attacks, authentication issues
2. **Performance**: Inefficient algorithms, N+1 queries, resource leaks
3. **Best Practices**: Code style, error handling, testing
4. **Docker Configuration**: Security, efficiency, best practices
5. **Kubernetes Manifests**: Resource limits, health checks, security policies

---

## Setting Up Gemini AI

### Step 1: Get API Key

**Option A: Google AI Studio (Recommended for Development)**

```bash
# 1. Go to https://aistudio.google.com/app/apikey
# 2. Click "Create API key"
# 3. Choose default project
# 4. Copy API key
# 5. Keep it secret!
```

**Option B: Vertex AI (Recommended for Production)**

```bash
# 1. Go to Google Cloud Console
# 2. Enable Vertex AI API
# 3. Create service account
# 4. Generate JSON key
# 5. Use in environment variable
```

### Step 2: Add to GitHub Secrets

```bash
# Go to: Repository → Settings → Secrets and variables → Actions
# Click "New repository secret"
# Name: GEMINI_API_KEY
# Value: your-api-key
```

### Step 3: Store Locally (Non-Git)

```bash
# Create .env.local (NOT committed to git)
echo "GEMINI_API_KEY=your-api-key" > .env.local

# Add to .gitignore
echo ".env.local" >> .gitignore
```

---

## How Gemini AI Review Works

### Code Review Flow

```
1. Developer Pushes Code
        ↓
2. GitHub Actions Triggered
        ↓
3. Get Changed Files
        ↓
4. Gemini AI Analysis
   ├─ General Code Review
   ├─ Security Analysis
   ├─ Performance Analysis
   └─ Kubernetes/Docker Validation
        ↓
5. Generate Markdown Report
        ↓
6. Comment on PR (if PR) or Log Results
        ↓
7. Fail/Pass Job Based on Severity
```

### Review Categories

#### 1. General Code Review
Analyzes for:
- Security vulnerabilities
- Performance concerns
- Best practice violations
- Bug risks

Example issues detected:
- SQL injection risks
- Hardcoded credentials
- Inefficient loops
- Missing error handling

#### 2. Security Review
Focused on:
- Authentication/Authorization
- Injection attacks (SQL, NoSQL, XSS, CSRF)
- Cryptography issues
- Dependency vulnerabilities
- Cloud security (AWS, Docker)

Example issues:
```java
// BAD - SQL Injection risk
String query = "SELECT * FROM users WHERE id = " + userId;

// GOOD - Parameterized query
String query = "SELECT * FROM users WHERE id = ?";
statement.setInt(1, userId);

// BAD - Hardcoded secret
private static final String API_KEY = "sk-1234567890";

// GOOD - Use environment variable
String apiKey = System.getenv("API_KEY");
```

#### 3. Performance Review
Checks for:
- Algorithm efficiency (Big O complexity)
- N+1 query problems
- Memory leaks
- Inefficient string operations
- Thread pool misconfiguration

Example issues:
```java
// BAD - O(n²) complexity
for (User user : users) {
    for (Order order : orders) {
        if (user.getId() == order.getUserId()) {
            // process...
        }
    }
}

// GOOD - Use HashMap for O(1) lookup
Map<Integer, List<Order>> ordersByUser = 
    orders.stream().collect(Collectors.groupingBy(Order::getUserId));
for (User user : users) {
    List<Order> userOrders = ordersByUser.get(user.getId());
    // process...
}

// BAD - String concatenation in loop
String result = "";
for (String item : items) {
    result += item + ",";  // Creates new String each iteration
}

// GOOD - Use StringBuilder
StringBuilder result = new StringBuilder();
for (String item : items) {
    result.append(item).append(",");
}
```

#### 4. Kubernetes/Docker Validation
Analyzes:
- Dockerfile security (multi-stage, non-root user)
- Resource management (CPU/memory limits)
- Health checks (readiness, liveness probes)
- Security context
- Volume mounts
- Image scanning

Example issues:
```yaml
# BAD - No health checks
containers:
- name: app
  image: myapp:latest
  # Missing probes!

# GOOD - Comprehensive health checks
containers:
- name: app
  image: myapp:latest
  readinessProbe:
    httpGet:
      path: /health
      port: 8080
    initialDelaySeconds: 30
    periodSeconds: 10
  livenessProbe:
    httpGet:
      path: /health
      port: 8080
    initialDelaySeconds: 60
    periodSeconds: 10
```

---

## Gemini AI Deployment Validation

### Validation Process

After deployment to Kubernetes, Gemini AI validates:

```
1. Pod Status
   - All pods running?
   - All pods ready?
   - No restarts?
        ↓
2. Service Status
   - LoadBalancer provisioned?
   - External IP assigned?
   - Ports correct?
        ↓
3. Application Logs
   - Any errors?
   - Any exceptions?
   - Performance acceptable?
        ↓
4. Resource Usage
   - CPU/Memory normal?
   - Not hitting limits?
        ↓
5. HPA Status
   - Configured correctly?
   - Metrics available?
        ↓
6. Gemini AI Analysis
   - Validates all checks passed
   - Produces final report
   - Determines PASS/FAIL
```

### Validation Report

Generated report includes:
```markdown
# Kubernetes Deployment Validation Report

## Summary
- Total Pods: 3
- Running: 3
- Ready: 3
- Unhealthy: 0

## Pod Status ✅
- All replicas running
- All probes passing
- No restart loops

## Service Status
- Type: LoadBalancer
- External IP: 1.2.3.4
- Health: ✅

## Application Health
- Error Count: 0
- Warnings: 0
- Exceptions: 0

## Gemini AI Analysis
✅ Overall Status: HEALTHY
✅ Ready for production traffic
✅ No issues detected

## Recommendations
1. Monitor the first 15 minutes of traffic
2. Validate response times are acceptable
3. Check business metrics in application
```

---

## Running Gemini AI Manually

### Code Review Only

```bash
# On your machine
python scripts/gemini_code_review.py \
    --api-key "your-api-key" \
    --changed-files "src/main/java/Example.java k8s/deployment.yml" \
    --include-security \
    --include-kubernetes

# Outputs:
# - review_output.md (human readable)
# - review_output.json (programmatic)
```

### Deployment Validation Only

```bash
python scripts/gemini_deployment_validation.py \
    --api-key "your-api-key" \
    --namespace "production" \
    --deployment "currency-conversion-service" \
    --image-uri "123456789.dkr.ecr.us-east-1.amazonaws.com/currency-conversion-service:v1"

# Outputs:
# - validation_report.md
# - validation_data.json
```

---

## Understanding Gemini AI Responses

### Severity Levels

**CRITICAL** (Deployment blocked)
- Security vulnerabilities
- Memory leaks
- Pods not running
- Application errors

**HIGH** (Warnings)
- Performance concerns
- Deprecated libraries
- Missing health checks
- Resource limit issues

**MEDIUM** (Suggestions)
- Style improvements
- Test coverage
- Documentation issues

**LOW** (Nice to have)
- Code cleanup
- Minor optimizations

### Report Interpretation

```markdown
## Critical Issues Found

### Issue 1: SQL Injection Risk
**Location**: UserRepository.java:45
**Severity**: CRITICAL
**Description**: Direct string concatenation in SQL query
**Current Code**: 
    String query = "SELECT * FROM users WHERE name = '" + name + "'";
**Recommended Fix**:
    String query = "SELECT * FROM users WHERE name = ?";
    PreparedStatement ps = conn.prepareStatement(query);
    ps.setString(1, name);

### Issue 2: Missing Health Endpoint
**Location**: deployment.yml:25
**Severity**: MEDIUM
**Description**: No readiness probe configured
**Current Code**: [no probe]
**Recommended Fix**: Add readiness probe
```

---

## Troubleshooting Gemini AI Integration

### Issue 1: API Key Not Working

```bash
# Test the API key
curl -X POST "https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent?key=$GEMINI_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"contents":[{"parts":[{"text":"Test"}]}]}'

# Expected: JSON response with generated content
# Error: Check API key is correct and API is enabled
```

### Issue 2: Rate Limiting

Gemini API has usage limits:
- Free tier: 60 RPM (requests per minute)
- Scaled tier: Higher limits available

Solution:
```bash
# Add retry logic in scripts
# Reduce frequency of reviews
# Upgrade to paid tier
```

### Issue 3: GitHub Actions Timeout

If Gemini AI takes too long:
```bash
# Increase timeout in workflow
timeout-minutes: 30  # Increase from default 360

# Or skip non-critical reviews
--include-security: false  # Only critical reviews
```

### Issue 4: Missing Results

```bash
# Check GitHub Actions logs:
# 1. Go to Repository → Actions
# 2. Click on failed workflow
# 3. Scroll to "Gemini AI Code Review" step
# 4. Check error messages

# Common issues:
# - API key not set in secrets
# - Network connectivity
# - File reading permissions
# - API quota exceeded
```

---

## Best Practices for Gemini AI Reviews

### 1. Regular Updates
- Keep Gemini dependencies updated
- Monitor Google AI updates
- Update prompt templates

### 2. Feedback Loop
- Review Gemini's suggestions
- Improve prompts based on feedback
- Track false positives

### 3. Escalation Process
```
Gemini AI Review
    ↓
Low Risk: Auto-Approve (INFO level issues)
    ↓
Medium Risk: Require Review (HIGH level issues)
    ↓
High Risk: Block Deployment (CRITICAL issues)
    ↓
Security: Always Manual Review (before prod)
```

### 4. Team Education
- Share insights from Gemini reviews
- Document common issues
- Create coding standards based on findings
- Regular training sessions

---

## Advanced Configurations

### Custom Prompts

To modify review criteria, edit scripts:

```python
# In gemini_code_review.py, customize:
def _create_security_prompt(self, content: str) -> str:
    return f"""
    Review for YOUR SPECIFIC NEEDS:
    1. Your custom check 1
    2. Your custom check 2
    3. Your custom check 3
    ...
    """
```

### Integration with Slack

Add to workflow:
```yaml
- name: Send Slack Notification
  uses: slackapi/slack-github-action@v1
  with:
    payload: |
      {
        "text": "Gemini AI Review: ${{ steps.gemini-review.outputs.result }}"
      }
```

### Email Notifications

```yaml
- name: Send Email
  uses: dawidd6/action-send-mail@v3
  with:
    server_address: smtp.gmail.com
    server_port: 465
    username: ${{ secrets.EMAIL_USERNAME }}
    password: ${{ secrets.EMAIL_PASSWORD }}
    subject: "Deployment Review: ${{ job.status }}"
    to: team@example.com
    body: |
      Gemini AI Code Review
      Status: ${{ steps.gemini-review.outputs.result }}
```

---

## Monitoring Gemini AI Usage

### Track API Calls

Add logging to scripts:
```python
# In gemini_code_review.py
import logging

logger = logging.getLogger(__name__)
logger.info(f"Gemini API call - Model: gemini-pro, Tokens: ~500")
```

### Cost Estimation

Free tier: 60 requests/minute = ~2,880/day
- Typical review: 1-2 requests
- Cost per review: Free (up to limit)

Paid tier: Pay per request
- $0.00075/1000 input tokens
- $0.003/1000 output tokens

---

## Success Metrics

Track these to measure effectiveness:

```
1. Issues Caught Early: X issues prevented reaching production
2. Time Saved: X hours of manual review saved
3. Security Improvements: X vulnerabilities detected
4. Performance Gains: X performance improvements implemented
5. Team Satisfaction: Feedback from team on usefulness
6. False Positive Rate: Issues incorrectly flagged
```

---

## Support & Resources

- [Gemini AI Documentation](https://ai.google.dev/docs)
- [API Reference](https://ai.google.dev/api/generate-content)
- [Examples and Recipes](https://ai.google.dev/examples)
- [FAQ](https://support.google.com/ai/answer/13343457)

---

## Example: Full CI/CD Flow with Gemini AI

```bash
# 1. Developer changes code
echo "List<User> users = getUsersFromDB(query);" > src/main/java/Example.java

# 2. Push to GitHub
git add .
git commit -m "feat: Load users from database"
git push origin feature-branch

# 3. Create Pull Request
# GitHub Actions auto-triggers

# 4. Gemini AI Analysis Starts
# [Running Code Review...]
# Detects: Possible SQL Injection in query parameter
# Detects: No pagination for large result sets
# Detects: Missing null checks

# 5. Report Posted to PR
# "❌ Gemini AI found 2 CRITICAL issues:
#   1. SQL Injection risk
#   2. Performance issue (no pagination)
#   
#  Fix these before merge"

# 6. Developer Fixes Issues
git commit -m "fix: Use PreparedStatement and add pagination"
git push

# 7. Gemini AI Reviews Again
# "✅ All critical issues resolved
#   Ready for merge"

# 8. Deploy to Main
# Merge PR → Triggers CD

# 9. Deployment Validation
# Gemini AI checks:
# - Pods running ✅
# - Health checks passing ✅
# - No errors in logs ✅
# - Performance metrics normal ✅
# 
# "✅ Deployment Successful - Ready for production"
```

---

**Last Updated**: 2024
**Maintained By**: Your Team
