#!/bin/bash

# GStreamer Media Distributor - Test Script
# Validates the installation and basic functionality

set -e

echo "🧪 GStreamer Media Distributor Test Suite"
echo "=========================================="

ERRORS=0

# Test 1: Check required files
echo "📁 Testing file structure..."
REQUIRED_FILES=(
    "docker-compose.yaml"
    "config/config.example.yml"
    "gstreamer-server/Dockerfile"
    "gstreamer-server/scripts/stream-manager.py"
    "web-control/Dockerfile" 
    "web-control/app.py"
    "web-control/templates/index.html"
)

for file in "${REQUIRED_FILES[@]}"; do
    if [ -f "$file" ]; then
        echo "  ✅ $file"
    else
        echo "  ❌ $file (missing)"
        ((ERRORS++))
    fi
done

# Check if Docker and Docker Compose are installed
echo ""
echo "🐳 Testing Docker environment..."
if command -v docker &> /dev/null; then
    echo "  ✅ Docker installed"
    if docker ps &> /dev/null; then
        echo "  ✅ Docker daemon running"
    else
        echo "  ❌ Docker daemon not running"
        ((ERRORS++))
    fi
else
    echo "  ❌ Docker not installed"
    ((ERRORS++))
fi

# Check for Docker Compose (v2 or v1)
if docker compose version &> /dev/null; then
    echo "  ✅ Docker Compose v2 installed"
elif command -v docker-compose &> /dev/null; then
    echo "  ✅ Docker Compose v1 installed"
else
    echo "  ❌ Docker Compose not installed"
    ((ERRORS++))
fi

# Test 3: Validate Docker Compose configuration
echo ""
echo "🔧 Testing Docker Compose configuration..."
if docker compose config &> /dev/null || docker-compose config &> /dev/null; then
    echo "  ✅ Docker Compose configuration valid"
else
    echo "  ❌ Docker Compose configuration invalid"
    ((ERRORS++))
fi

# Test 4: Check Python syntax
echo ""
echo "🐍 Testing Python syntax..."
if python3 -m py_compile gstreamer-server/scripts/stream-manager.py 2>/dev/null; then
    echo "  ✅ stream-manager.py syntax valid"
else
    echo "  ❌ stream-manager.py syntax errors"
    ((ERRORS++))
fi

if python3 -m py_compile web-control/app.py 2>/dev/null; then
    echo "  ✅ app.py syntax valid"
else
    echo "  ❌ app.py syntax errors"
    ((ERRORS++))
fi

# Test 5: Check configuration
echo ""
echo "⚙️  Testing configuration..."
if [ -f "config/config.yml" ]; then
    echo "  ✅ config.yml exists"
    if python3 -c "import yaml; yaml.safe_load(open('config/config.yml'))" 2>/dev/null; then
        echo "  ✅ config.yml is valid YAML"
    else
        echo "  ❌ config.yml has YAML syntax errors"
        ((ERRORS++))
    fi
else
    echo "  ⚠️  config.yml not found (run ./setup.sh first)"
fi

# Test 6: Check network ports
echo ""
echo "🌐 Testing network ports..."
if ! netstat -tuln 2>/dev/null | grep -q ":8080 "; then
    echo "  ✅ Port 8080 available"
else
    echo "  ⚠️  Port 8080 already in use"
fi

if ! netstat -tuln 2>/dev/null | grep -q ":8081 "; then
    echo "  ✅ Port 8081 available"
else
    echo "  ⚠️  Port 8081 already in use"
fi

# Test 7: Check GStreamer availability (for local testing)
echo ""
echo "🎬 Testing GStreamer availability..."
if command -v gst-launch-1.0 &> /dev/null; then
    echo "  ✅ GStreamer CLI tools available (for local testing)"
    
    # Test basic GStreamer functionality
    if timeout 2 gst-launch-1.0 videotestsrc num-buffers=1 ! fakesink &> /dev/null; then
        echo "  ✅ GStreamer basic functionality working"
    else
        echo "  ⚠️  GStreamer basic test failed"
    fi
else
    echo "  ⚠️  GStreamer CLI tools not available (will use Docker)"
fi

# Summary
echo ""
echo "📊 Test Summary"
echo "==============="

if [ $ERRORS -eq 0 ]; then
    echo "🎉 All tests passed! Your installation is ready."
    echo ""
    echo "Next steps:"
    echo "1. Run ./setup.sh if you haven't already"
    echo "2. Edit config/config.yml with your display settings"
    echo "3. Start with: docker compose up -d"
    echo "4. Access web interface: http://localhost:8080"
else
    echo "❌ $ERRORS test(s) failed. Please fix the issues above."
    exit 1
fi
