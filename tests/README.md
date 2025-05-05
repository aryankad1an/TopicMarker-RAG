# TopicMarker-RAG Tests

This directory contains all the tests for the TopicMarker-RAG project.

## Directory Structure

- `unit/`: Unit tests for individual components
- `integration/`: Integration tests that test multiple components together
- `api/`: Tests for the API endpoints
- `html/`: HTML test files for manual testing

## Running Tests

### Unit Tests

To run unit tests:

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
python test_refine_routes.py
```

### HTML Tests

To run HTML tests, start the test page server:

```bash
cd tests
python serve_test_page.py
```

Then open your browser and navigate to http://localhost:8080/test_api.html
