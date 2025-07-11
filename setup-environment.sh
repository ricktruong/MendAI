#!/bin/bash

# MendAI Environment Setup Script
# Detects your environment and provides appropriate setup instructions

echo "🔍 Detecting your environment..."

# Check if running on Jetson (multiple indicators)
if [ -f /etc/nv_tegra_release ] || [ "$(uname -m)" = "aarch64" ] && [ -d /etc/nv ]; then
    echo "✅ Detected: NVIDIA Jetson Device"
    echo "📋 JetPack version: $(cat /etc/nv_tegra_release | cut -d' ' -f2 | cut -d'.' -f1,2)"
    echo "📋 Architecture: $(uname -m)"
    echo ""
    echo "🚀 Running Jetson setup..."
    ./setup-jetson.sh
elif command -v nvidia-smi &> /dev/null; then
    echo "✅ Detected: Regular Linux with NVIDIA GPU"
    echo "⚠️  Note: This setup will use CPU PyTorch for compatibility"
    echo "   For GPU acceleration, consider using NVIDIA Docker runtime"
    echo ""
    echo "🚀 Running regular Linux setup..."
    ./setup-jetson.sh
else
    echo "✅ Detected: Regular Linux (no NVIDIA GPU)"
    echo "⚠️  Note: GPU services will run with CPU PyTorch"
    echo "   This is fine for development and testing"
    echo ""
    echo "🚀 Running regular Linux setup..."
    ./setup-jetson.sh
fi

echo ""
echo "📚 Environment-specific notes:"
echo ""
if [ -f /etc/nv_tegra_release ] || [ "$(uname -m)" = "aarch64" ] && [ -d /etc/nv ]; then
    echo "🎯 Jetson Environment:"
    echo "   - Full GPU acceleration available"
    echo "   - Uses NVIDIA's pre-built PyTorch for Jetson"
    echo "   - Optimized for ARM64 architecture"
elif command -v nvidia-smi &> /dev/null; then
    echo "🎯 Regular Linux with NVIDIA GPU:"
    echo "   - GPU acceleration available with NVIDIA Docker runtime"
    echo "   - Uses CPU PyTorch by default for compatibility"
    echo "   - Can be upgraded to GPU PyTorch if needed"
else
    echo "🎯 Regular Linux (no GPU):"
    echo "   - CPU-only operation"
    echo "   - Perfect for development and testing"
    echo "   - Can deploy to Jetson later for production"
fi 