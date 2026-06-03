#!/bin/bash

echo "================================"
echo "M1 Ingestion Pipeline Tests"
echo "================================"
echo ""

echo "Running Chunker Tests..."
python -m pytest tests/test_chunker.py -v --tb=short
CHUNKER_RESULT=$?
echo ""

echo "Running Parser Tests..."
python -m pytest tests/test_parser.py -v --tb=short
PARSER_RESULT=$?
echo ""

echo "Running Metadata Tests..."
python -m pytest tests/test_metadata.py -v --tb=short
METADATA_RESULT=$?
echo ""

echo "================================"
echo "Test Summary"
echo "================================"
if [ $CHUNKER_RESULT -eq 0 ]; then
    echo "✓ Chunker Tests: PASSED"
else
    echo "✗ Chunker Tests: FAILED"
fi

if [ $PARSER_RESULT -eq 0 ]; then
    echo "✓ Parser Tests: PASSED"
else
    echo "✗ Parser Tests: FAILED"
fi

if [ $METADATA_RESULT -eq 0 ]; then
    echo "✓ Metadata Tests: PASSED"
else
    echo "✗ Metadata Tests: FAILED"
fi
echo ""

if [ $CHUNKER_RESULT -eq 0 ] && [ $PARSER_RESULT -eq 0 ] && [ $METADATA_RESULT -eq 0 ]; then
    echo "All tests passed! ✓"
    exit 0
else
    echo "Some tests failed!"
    exit 1
fi
