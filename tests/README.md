# TopicMarker-RAG Tests

This directory contains all the tests for the TopicMarker-RAG project.

## Directory Structure

- `unit/`: Unit tests for individual components
- `integration/`: Integration tests that test multiple components together
- `api/`: Tests for the API endpoints
- `html/`: HTML test files for manual testing

## Running Tests

### Using the Test Runner

The project includes a test runner script that can run different categories of tests:

```bash
# Run all tests
cd tests
python run_tests.py --all

# Run only unit tests
python run_tests.py --unit

# Run only API tests (requires the API server to be running)
python run_tests.py --api

# Run a specific API test file
python run_tests.py --api-test refine_routes  # Runs test_refine_routes.py
python run_tests.py --api-test rag_routes     # Runs test_rag_routes.py

# Run only integration tests
python run_tests.py --integration
```

#### Notes on the Test Runner

- The `--api` option will run all API tests sequentially, with each test file running as a separate process
- The `--api-test` option allows you to run a specific API test file, which is useful for testing individual endpoints
- The test runner will check if the API server is running before attempting to run API tests
- If the API server is not running, the test runner will display an error message and exit

### Unit Tests

To run unit tests directly:

```bash
cd tests/unit
python -m unittest discover
```

### API Tests

To run API tests, make sure the API server is running first:

```bash
# Start the API server
cd ../..  # Go to project root
python -m app.main

# In another terminal
cd tests/api
python test_refine_routes.py  # Test refine routes
python test_rag_routes.py     # Test other RAG routes
```

#### Notes on API Tests

- The tests include increased timeout values (30-60 seconds) to accommodate LLM processing and web crawling
- Tests will automatically skip if the API server is not running
- If a test times out, it will be marked as skipped with a message indicating the timeout
- For endpoints that involve crawling or extensive LLM processing, timeouts may still occur if the processing takes longer than expected

### HTML Tests

To run HTML tests, start the test page server:

```bash
cd tests
python serve_test_page.py
```

Then open your browser and navigate to http://localhost:8080/test_api.html
