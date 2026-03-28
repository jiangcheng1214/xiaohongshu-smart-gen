# Testing Guide

## Overview

This project follows Test-Driven Development (TDD) principles with comprehensive test coverage for all core modules.

## Test Structure

```
tests/
├── __init__.py              # Test suite init
├── conftest.py              # Pytest fixtures and configuration
├── test_config.py           # Config module tests
├── test_session.py          # Session management tests
├── test_cli.py              # CLI command tests
├── test_cover.py            # Cover generator tests
├── test_content.py          # Content generator tests
├── test_images.py           # Image searcher tests (NEW)
└── test_telegram.py         # Telegram sender tests (NEW)
```

## Running Tests

### Run All Tests

```bash
# Using pytest directly
python -m pytest tests/ -v

# Using the test runner
python run_tests.py
```

### Run with Coverage

```bash
# Generate coverage report
python run_tests.py --coverage

# Or with pytest
python -m pytest tests/ --cov=scripts --cov-report=term-missing --cov-report=html
```

Coverage target: **80%+** (branches, functions, lines, statements)

### Run Specific Tests

```bash
# Run specific test file
python -m pytest tests/test_images.py -v

# Run tests matching pattern
python -m pytest tests/ -k "test_search" -v

# Run by marker
python -m pytest tests/ -m "unit" -v
```

## Test Coverage by Module

| Module | Test File | Coverage Status |
|--------|-----------|-----------------|
| `config.py` | `test_config.py` | ✅ Complete |
| `session.py` | `test_session.py` | ✅ Complete |
| `cli.py` | `test_cli.py` | ✅ Complete |
| `content.py` | `test_content.py` | ✅ Complete |
| `cover.py` | `test_cover.py` | ✅ Complete |
| `images.py` | `test_images.py` | ✅ **NEW** |
| `telegram.py` | `test_telegram.py` | ✅ **NEW** |

## TDD Workflow

### 1. Red - Write Failing Test

```python
def test_new_feature():
    """Test new feature that doesn't exist yet"""
    result = new_function()
    assert result == expected
```

### 2. Run Test - Verify it Fails

```bash
python -m pytest tests/test_new.py -v
# Should show FAILED
```

### 3. Green - Write Minimal Implementation

```python
def new_function():
    return expected  # Minimal code to pass
```

### 4. Run Test - Verify it Passes

```bash
python -m pytest tests/test_new.py -v
# Should show PASSED
```

### 5. Refactor - Improve Code

```python
def new_function():
    # Improved implementation
    if condition:
        return calculate_expected()
    return default_expected()
```

### 6. Verify Coverage

```bash
python -m pytest tests/ --cov=scripts --cov-report=term-missing
# Should show 80%+ coverage
```

## Test Patterns

### Unit Tests

Test individual functions in isolation:

```python
class TestImageSearcher(unittest.TestCase):
    def test_build_queries_default(self):
        searcher = ImageSearcher()
        queries = searcher._build_queries("iPhone 15", [])
        self.assertEqual(queries, ["iPhone 15", "iPhone 15 评测", "iPhone 15 测评"])
```

### Integration Tests

Test module interactions:

```python
@patch('scripts.xhs_cli.core.images.subprocess.run')
def test_search_full_flow_with_ai(self, mock_run):
    searcher = self._create_searcher()
    session = self._create_session()
    downloaded = searcher.search(session, count=3)
    self.assertGreater(len(downloaded), 0)
```

### Edge Cases

Test boundary conditions and error paths:

```python
def test_search_empty_keywords(self):
    """测试空关键词的搜索"""
    # Test with empty keywords
    queries = searcher._build_queries("Topic", [])
    self.assertGreater(len(queries), 0)

def test_search_with_long_topic(self):
    """测试长话题的占位符创建"""
    session = self._create_session(topic="a" * 50)
    downloaded = searcher.search(session, count=1)
    self.assertTrue(downloaded[0].exists())
```

## Mocking External Dependencies

### Mock File System

```python
def test_with_temp_dir(self):
    with tempfile.TemporaryDirectory() as temp_dir:
        workspace = Path(temp_dir) / "workspace"
        workspace.mkdir()
        # Test with isolated workspace
```

### Mock Subprocess Calls

```python
@patch('scripts.xhs_cli.core.images.subprocess.run')
def test_run_search_success(self, mock_run):
    mock_run.return_value = Mock(returncode=0)
    result = searcher._run_search(script, query, output)
    self.assertTrue(result)
```

### Mock Network Requests

```python
@patch('scripts.xhs_cli.core.telegram.requests.post')
def test_send_photo_success(self, mock_post):
    mock_response = Mock()
    mock_response.raise_for_status = Mock()
    mock_post.return_value = mock_response
    result = sender.send_photo(photo_path, caption)
    self.assertTrue(result)
```

## Coverage Goals

- **Branch Coverage**: 80%+
- **Function Coverage**: 80%+
- **Line Coverage**: 80%+
- **Statement Coverage**: 80%+

## Continuous Integration

Run tests on every commit:

```bash
# Pre-commit hook
python -m pytest tests/ -v --cov-fail-under=80

# Or using test runner
python run_tests.py --coverage
```

## Troubleshooting

### Tests Fail with Import Errors

```bash
# Ensure project root is in Python path
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
python -m pytest tests/ -v
```

### Coverage Report Not Generated

```bash
# Install pytest-cov
pip install pytest-cov

# Re-run with coverage
python -m pytest tests/ --cov=scripts --cov-report=html
```

### Mock Not Working

```bash
# Check mock path matches import path
# If module does: from scripts.xhs_cli.core import images
# Mock should be: scripts.xhs_cli.core.images.function_name
```

## Test Maintenance

### When Code Changes

1. Update affected tests
2. Ensure coverage stays above 80%
3. Add tests for new features
4. Remove obsolete tests

### When Tests Fail

1. Check if test is valid (not testing implementation details)
2. Verify mock setup is correct
3. Check for external dependencies (network, file system)
4. Run with verbose output: `pytest -vv`

## Best Practices

1. **Test behavior, not implementation**
   - ✅ Test: "Function returns correct result for valid input"
   - ❌ Test: "Function calls subprocess with specific arguments"

2. **One assertion per test**
   - ✅ Separate tests for different conditions
   - ❌ Multiple assertions in one test

3. **Use descriptive test names**
   - ✅ `test_search_with_long_topic_creates_valid_placeholders`
   - ❌ `test_search_3`

4. **Mock external dependencies**
   - File system operations
   - Network requests
   - Subprocess calls
   - Database operations

5. **Test edge cases**
   - Null/None values
   - Empty strings/lists
   - Invalid types
   - Boundary values
   - Error paths

## Resources

- [Pytest Documentation](https://docs.pytest.org/)
- [unittest Documentation](https://docs.python.org/3/library/unittest.html)
- [TDD Best Practices](https://martinfowler.com/bliki/TestDrivenDevelopment.html)
