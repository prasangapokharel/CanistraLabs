# API Testing Suite

This directory contains comprehensive API endpoint tests for the ICP Hosting Platform.

## Quick Start

```bash
# Run all tests with default settings
./run_tests.sh

# Run tests against different environment
./run_tests.sh https://your-api-domain.com your-email@domain.com your-password

# Run tests with custom parameters
python3 test_api_endpoints.py --base-url http://localhost:8000 --email test@example.com --password testpass --output results.json
```

## Test Coverage

The test suite covers all major API endpoints:

### 🔐 Authentication
- User signup and login
- Token refresh mechanism
- Password reset flow
- Secure logout

### 📁 Project Management
- Create, read, update, delete projects
- Project listing and filtering
- Project configuration management

### 💰 Wallet Operations
- Wallet identity management
- Balance checking and refresh
- Funding status verification

### 🚀 Deployment
- Project deployment to IC canisters
- Canister status monitoring
- Deployment history tracking

### 🌐 Domain Management
- Custom domain setup
- DNS verification
- Domain status monitoring

## Test Files

- `test_api_endpoints.py` - Main comprehensive test suite
- `run_tests.sh` - Simple test runner script
- `requirements.txt` - Python dependencies
- `README.md` - This documentation

## Requirements

- Python 3.7+
- aiohttp library
- Running backend server

## Output

Tests generate JSON reports with:
- Test success/failure status
- Response details
- Performance metrics
- Error diagnostics

Example output:
```
🧪 API Endpoint Tests - Summary
===============================
Total Tests: 25
Passed: 23 ✅
Failed: 2 ❌
Success Rate: 92.0%
Duration: 0:00:45
===============================
```

## Configuration

The test suite uses these defaults:
- Base URL: `http://localhost:8000`
- Test Email: `prasangaramanpokharel@gmail.com`
- Password: `SecurePassword123!`

Override these with command-line arguments or environment variables.

## Troubleshooting

1. **Connection errors**: Ensure the backend server is running
2. **Authentication failures**: Check that test credentials are valid
3. **Permission errors**: Verify the test user has required permissions
4. **Timeout errors**: Increase timeout values for slower environments

## Integration

This test suite can be integrated into CI/CD pipelines:

```yaml
# Example GitHub Actions step
- name: Run API Tests
  run: |
    cd testing
    ./run_tests.sh $API_BASE_URL $TEST_EMAIL $TEST_PASSWORD
```