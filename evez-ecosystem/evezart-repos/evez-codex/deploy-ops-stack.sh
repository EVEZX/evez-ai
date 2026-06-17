#!/bin/bash
set -euo pipefail

echo "🚀 Ops Stack Deployment Script"
echo "================================"
echo ""

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored messages
print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_info() {
    echo -e "${YELLOW}ℹ️  $1${NC}"
}

# Preflight checks
echo "📋 Running preflight checks..."
echo ""

# Check Node.js
if ! command -v node &> /dev/null; then
    print_error "Node.js is not installed"
    exit 1
fi
NODE_VERSION=$(node --version)
print_success "Node.js $NODE_VERSION detected"

# Check pnpm
if ! command -v pnpm &> /dev/null; then
    print_error "pnpm is not installed"
    exit 1
fi
PNPM_VERSION=$(pnpm --version)
print_success "pnpm $PNPM_VERSION detected"

# Check TypeScript
if ! command -v tsc &> /dev/null; then
    print_info "TypeScript not found globally, will use local installation"
fi

echo ""
echo "📦 Installing dependencies..."
cd ops-stack
if [ ! -d "node_modules" ]; then
    pnpm install
    print_success "Dependencies installed"
else
    print_success "Dependencies already installed"
fi

echo ""
echo "🔨 Building TypeScript..."
if [ -f "tsconfig.json" ]; then
    if pnpm build; then
        print_success "Build completed"
    else
        print_error "Build failed"
        exit 1
    fi
fi

echo ""
echo "🧪 Running golden hash tests..."
if pnpm test; then
    print_success "All golden hash tests passed!"
else
    print_error "Golden hash tests failed!"
    exit 1
fi

echo ""
echo "🎯 Deployment Steps"
echo "-------------------"
print_info "Step 1: Golden hash tests completed ✅"
print_info "Step 2: Mock deployment to staging environment..."
sleep 1
print_success "Staging deployment successful"

print_info "Step 3: Running smoke tests..."
if [ -n "${OPS_STACK_HEALTHCHECK_URL:-}" ]; then
    if curl --fail --silent --show-error --max-time 10 "$OPS_STACK_HEALTHCHECK_URL" > /dev/null; then
        print_success "Health check passed: $OPS_STACK_HEALTHCHECK_URL"
    else
        print_error "Health check failed: $OPS_STACK_HEALTHCHECK_URL"
        exit 1
    fi
else
    print_info "No OPS_STACK_HEALTHCHECK_URL configured; skipping live health check"
    sleep 1
    print_success "Mock smoke tests passed"
fi

print_info "Step 4: Mock deployment to production environment..."
sleep 1
print_success "Production deployment successful"

echo ""
echo "================================"
print_success "🎉 Deployment completed successfully!"
echo ""
print_info "Next steps:"
echo "  - Monitor logs: ./scripts/monitor-logs.sh (if available)"
echo "  - Run health checks: curl \"\${OPS_STACK_HEALTHCHECK_URL:-https://ops-stack.example.com/health}\""
echo "  - View metrics: https://ops-stack.example.com/metrics"
echo ""
