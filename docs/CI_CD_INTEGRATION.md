# CI/CD Integration Guide for Aether-Thread

This guide shows how to integrate Aether-Thread thread-safety checks into your CI/CD pipeline.

## Quick Deploy Commands

```bash
# Installation
pip install aether-thread

# Run checks in CI/CD
aether check src/ --free-threaded    # Find thread-safety issues
aether status                         # Verify environment
```

---

## GitHub Actions

### Workflow: `.github/workflows/thread-safety.yml`

```yaml
name: Thread-Safety Check

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main, develop]

jobs:
  check-thread-safety:
    runs-on: ubuntu-latest
    
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Install Aether-Thread
        run: pip install aether-thread
      
      - name: Check thread-safety
        run: aether check src/ --free-threaded --verbose
        continue-on-error: false
      
      - name: Check environment
        run: aether status
      
      - name: Profile performance (optional)
        run: aether profile tests/benchmark.py --max-threads 32
        continue-on-error: true
```

### Workflow: Pre-Commit Hook

```yaml
# .github/workflows/pre-commit.yml
name: Pre-Commit Checks

on:
  pull_request:

jobs:
  validate:
    runs-on: ubuntu-latest
    
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        run: |
          pip install aether-thread
          pip install -r requirements.txt
      
      - name: Aether Thread-Safety Audit
        run: |
          echo "🔍 Running thread-safety audit..."
          aether check src/ --free-threaded
          
          if [ $? -eq 0 ]; then
            echo "✅ All thread-safety checks passed!"
          else
            echo "❌ Thread-safety issues found - see above"
            exit 1
          fi
      
      - name: Environment Validation
        run: aether status --verbose
```

---

## GitLab CI

### Configuration: `.gitlab-ci.yml`

```yaml
stages:
  - check
  - build
  - test

thread-safety:
  stage: check
  image: python:3.11
  
  script:
    - pip install aether-thread
    - echo "🔍 Checking thread-safety..."
    - aether check src/ --free-threaded --verbose
    - echo "✅ Thread-safety check passed!"
  
  allow_failure: false
  
  only:
    - merged_requests
    - main
    - develop

free-threaded-validation:
  stage: check
  image: python:3.13
  
  script:
    - pip install aether-thread
    - echo "🟢 Validating free-threaded Python readiness..."
    - aether status --verbose
    - aether check src/ --free-threaded
  
  only:
    - tags
    - main
```

---

## Jenkins

### Pipeline Script: `Jenkinsfile`

```groovy
pipeline {
    agent any
    
    stages {
        stage('Setup') {
            steps {
                script {
                    sh 'python3 -m venv venv'
                    sh '. venv/bin/activate && pip install aether-thread'
                }
            }
        }
        
        stage('Thread-Safety Check') {
            steps {
                script {
                    sh '. venv/bin/activate && aether check src/ --free-threaded --verbose'
                }
            }
        }
        
        stage('Environment Validation') {
            steps {
                script {
                    sh '. venv/bin/activate && aether status'
                }
            }
        }
        
        stage('Performance Profile') {
            steps {
                script {
                    catchError(buildResult: 'SUCCESS', stageResult: 'UNSTABLE') {
                        sh '. venv/bin/activate && aether profile tests/benchmark.py --max-threads 32'
                    }
                }
            }
        }
    }
    
    post {
        always {
            cleanWs()
        }
        failure {
            mail to: '${DEFAULT_RECIPIENTS}',
                 subject: "❌ Thread-Safety Check Failed: ${JOB_NAME}",
                 body: "See ${BUILD_URL} for details"
        }
    }
}
```

---

## CircleCI

### Configuration: `.circleci/config.yml`

```yaml
version: 2.1

jobs:
  thread-safety-check:
    docker:
      - image: cimg/python:3.11
    
    steps:
      - checkout
      
      - run:
          name: Install Aether-Thread
          command: pip install aether-thread
      
      - run:
          name: Check Thread-Safety
          command: |
            echo "🔍 Running thread-safety audit..."
            aether check src/ --free-threaded --verbose
      
      - run:
          name: Validate Environment
          command: aether status

  free-threaded-validation:
    docker:
      - image: cimg/python:3.13
    
    steps:
      - checkout
      
      - run:
          name: Install Aether-Thread
          command: pip install aether-thread
      
      - run:
          name: Validate Free-Threaded Readiness
          command: |
            aether status --verbose
            aether check src/ --free-threaded

workflows:
  version: 2
  
  pre-commit:
    jobs:
      - thread-safety-check:
          filters:
            branches:
              only:
                - main
                - develop
                - /^feature\/.*/
  
  release:
    jobs:
      - free-threaded-validation:
          filters:
            tags:
              only: /^v.*/
```

---

## Pre-Commit Hook

### File: `.pre-commit-config.yaml`

```yaml
repos:
  - repo: local
    hooks:
      - id: aether-thread-check
        name: Aether Thread-Safety Check
        entry: aether check src/ --free-threaded
        language: system
        types: [python]
        pass_filenames: false
        stages: [commit]
      
      - id: aether-status
        name: Aether GIL Status
        entry: aether status
        language: system
        pass_filenames: false
        stages: [commit]
        always_run: true

  # Combine with other checks
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.4.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: mixed-line-ending
      - id: requirements-txt-fixer
```

### Setup:

```bash
pip install pre-commit
pre-commit install
pre-commit run --all-files
```

---

## GitHub Actions: Detailed Strategy

### Strategy 1: Strict Mode (Fail on Any Issue)

```yaml
jobs:
  safety-check:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - run: pip install aether-thread
      
      - name: Run strict check
        run: |
          aether check src/ --free-threaded
          if [ $? -ne 0 ]; then
            echo "❌ Thread-safety issues found!"
            exit 1
          fi
```

### Strategy 2: Warning Mode (Report but Don't Fail)

```yaml
jobs:
  safety-advisory:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - run: pip install aether-thread
      
      - name: Run advisory check
        run: |
          echo "⚠️ Running thread-safety advisory..."
          aether check src/ --free-threaded --verbose || true
          echo "Review warnings above"
```

### Strategy 3: Grade-Based (Fail on Critical Only)

```yaml
jobs:
  safety-graded:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - run: pip install aether-thread
      
      - name: Check for critical issues
        run: |
          OUTPUT=$(aether check src/ --free-threaded 2>&1)
          
          if echo "$OUTPUT" | grep -q "🔴 CRASH"; then
            echo "❌ Critical (crash risk) issues found!"
            echo "$OUTPUT"
            exit 1
          fi
          
          if echo "$OUTPUT" | grep -q "🟠 SAFETY"; then
            echo "⚠️ Safety issues found (non-critical)"
            echo "$OUTPUT"
            exit 0
          fi
          
          echo "✅ No critical issues"
```

---

## Best Practices

### 1. Version Pinning
```yaml
# Always pin the version
pip install aether-thread==0.3.0
```

### 2. Environment-Specific Checks
```bash
# For Python 3.13+ free-threaded
if python -c "import sys; sys.exit(not hasattr(sys, '_is_gil_enabled'))"; then
  aether check src/ --free-threaded
fi
```

### 3. Staged Rollout
```bash
# Phase 1: Advisory (report only)
aether check src/ --free-threaded || true

# Phase 2: Warning (report issues, don't fail)
aether check src/ --free-threaded

# Phase 3: Enforce (fail on issues)
aether check src/ --free-threaded || exit 1
```

### 4. Combine with Other Checks
```yaml
# In .github/workflows/ci.yml
- run: black --check src/     # Code formatting
- run: flake8 src/            # Linting
- run: mypy src/              # Type checking
- run: aether check src/ --free-threaded  # Thread-safety
```

### 5. Performance Profiling in Release
```yaml
release:
  needs: [lint, test, safety-check]
  if: startsWith(github.ref, 'refs/tags/v')
  runs-on: ubuntu-latest
  steps:
    - uses: actions/checkout@v3
    - uses: actions/setup-python@v4
    - run: pip install aether-thread
    - name: Profile performance
      run: aether profile tests/benchmark.py --max-threads 32
```

---

## Exit Codes

```
0  = ✅ All checks passed
1  = ❌ Issues found or error occurred
```

Use this in your CI/CD:
```bash
aether check src/ --free-threaded
EXIT_CODE=$?

if [ $EXIT_CODE -eq 0 ]; then
  echo "✅ Deploy OK"
else
  echo "❌ Fix issues before deploying"
  exit 1
fi
```

---

## Common Issues & Solutions

### Issue: "aether: command not found"
**Solution:**
```bash
pip install aether-thread
# Or use: python -m aether.cli
```

### Issue: "ModuleNotFoundError: No module named 'aether'"
**Solution:**
```bash
pip install -e .  # Install in editable mode
# Then use: aether check src/
```

### Issue: Slow checks on large codebase
**Solution:**
```bash
# Use --verbose sparingly
aether check src/    # Fast
aether check . --all --verbose --deep-scan  # Slower but thorough
```

### Issue: False positives on protected code
**Solution:**
```bash
# Review flagged issues
aether check src/ --free-threaded --verbose

# If safe, add suppress comment:
# aether: ignore=race_condition_on_x
```

---

## Example: Complete CI/CD Pipeline

```yaml
# .github/workflows/complete-pipeline.yml
name: Complete Quality Pipeline

on: [push, pull_request]

jobs:
  quality:
    runs-on: ubuntu-latest
    
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      # Install tools
      - run: |
          pip install -e .
          pip install aether-thread black flake8 mypy pytest
      
      # Code quality
      - run: black --check src/
      - run: flake8 src/
      - run: mypy src/
      
      # Thread-safety (NEW!)
      - run: aether check src/ --free-threaded
      
      # Tests
      - run: pytest
      
      # Success!
      - run: echo "✅ All quality checks passed!"
```

---

## Running Locally (Before Commit)

```bash
# Install pre-commit hook
pip install pre-commit
pre-commit install

# Run manually
aether check src/ --free-threaded
aether status

# Or use Docker
docker run -v $(pwd):/app python:3.11 bash -c "
  cd /app
  pip install aether-thread
  aether check src/ --free-threaded
"
```

---

## Troubleshooting CI/CD Integration

### Debug mode:
```bash
aether check src/ --free-threaded --verbose
```

### Check environment:
```bash
aether status --verbose
```

### Test locally first:
```bash
# Mimic CI environment
python -m venv ci_test
source ci_test/bin/activate
pip install aether-thread
aether check src/ --free-threaded
```

---

Ready to deploy! Start with your platform:
- **GitHub Actions:** Copy the workflow example above
- **GitLab:** Update `.gitlab-ci.yml`
- **Jenkins:** Use the `Jenkinsfile` example  
- **Local:** Set up pre-commit hooks

