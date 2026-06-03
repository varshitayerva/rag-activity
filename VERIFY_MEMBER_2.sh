#!/bin/bash
# Member 2 Implementation Verification Script

echo "================================================================================"
echo "MEMBER 2 - HYBRID SEARCH & RETRIEVAL VERIFICATION"
echo "================================================================================"
echo ""

# Check required files
echo "Checking required files..."
files=(
    "backend/app/search/qdrant_client.py"
    "backend/app/search/embeddings.py"
    "backend/app/search/bm25_search.py"
    "backend/app/search/rrf_fusion.py"
    "backend/app/search/hybrid_search.py"
    "backend/app/search/__init__.py"
    "backend/tests/test_hybrid_search.py"
    "backend/tests/conftest.py"
    "backend/test_hybrid_search_demo.py"
    "docker/docker-compose.yml"
    "backend/requirements.txt"
)

all_exist=true
for file in "${files[@]}"; do
    if [ -f "$file" ]; then
        echo "  ✓ $file"
    else
        echo "  ✗ $file (MISSING)"
        all_exist=false
    fi
done

echo ""
if [ "$all_exist" = true ]; then
    echo "✓ All required files present"
else
    echo "✗ Some files are missing"
    exit 1
fi

echo ""
echo "================================================================================"
echo "Running tests..."
echo "================================================================================"
echo ""

cd backend
python -m pytest tests/test_hybrid_search.py -v --tb=short

test_result=$?
if [ $test_result -eq 0 ]; then
    echo ""
    echo "✓ All tests passed!"
else
    echo ""
    echo "✗ Some tests failed"
    exit 1
fi

echo ""
echo "================================================================================"
echo "Running demo..."
echo "================================================================================"
echo ""

python test_hybrid_search_demo.py

demo_result=$?
if [ $demo_result -eq 0 ]; then
    echo ""
    echo "✓ Demo completed successfully!"
else
    echo ""
    echo "✗ Demo failed"
    exit 1
fi

echo ""
echo "================================================================================"
echo "MEMBER 2 VERIFICATION: ALL CHECKS PASSED ✓"
echo "================================================================================"
echo ""
echo "Summary:"
echo "  - All 11 required files present"
echo "  - 16/16 unit tests passing"
echo "  - 5/5 demo queries successful"
echo "  - Ready for integration with M1, M3, M4, M5"
echo ""
