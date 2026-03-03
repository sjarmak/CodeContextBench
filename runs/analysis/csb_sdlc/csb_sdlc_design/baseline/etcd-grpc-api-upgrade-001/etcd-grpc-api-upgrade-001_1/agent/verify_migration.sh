#!/bin/bash

# Verification script for gRPC migration
# This script checks that all grpc.Dial/DialContext calls have been properly migrated to grpc.NewClient

cd /ccb_crossrepo/src || exit 1

echo "=== gRPC Migration Verification ==="
echo ""

found_issues=0

# Check for remaining grpc.Dial calls (excluding vendor and generated code)
echo "Checking for remaining grpc.Dial( calls..."
if grep -r "grpc\.Dial(" --include="*.go" . | grep -v vendor | grep -v "\.pb\." | grep -v "NewClient"; then
    echo "ERROR: Found grpc.Dial( calls that may not have been migrated"
    found_issues=$((found_issues + 1))
fi

# Check for remaining grpc.DialContext calls (excluding vendor and generated code)
echo ""
echo "Checking for remaining grpc.DialContext( calls..."
if grep -r "grpc\.DialContext(" --include="*.go" . | grep -v vendor | grep -v "\.pb\." | grep -v "staticcheck"; then
    echo "ERROR: Found grpc.DialContext( calls that may not have been migrated"
    found_issues=$((found_issues + 1))
fi

# Check that grpc.NewClient is present in expected files
echo ""
echo "Verifying grpc.NewClient is present in migrated files..."
declare -a FILES=(
    "kubernetes/pkg/kubelet/apis/podresources/client.go"
    "kubernetes/pkg/kubelet/cm/devicemanager/plugin/v1beta1/client.go"
    "kubernetes/pkg/volume/csi/csi_client.go"
    "kubernetes/pkg/serviceaccount/externaljwt/plugin/plugin.go"
    "etcd/server/embed/etcd.go"
    "etcd/client/v3/client.go"
)

for file in "${FILES[@]}"; do
    if [ -f "$file" ]; then
        if grep -q "grpc\.NewClient" "$file"; then
            echo "✓ $file contains grpc.NewClient"
        else
            echo "✗ $file does NOT contain grpc.NewClient"
            found_issues=$((found_issues + 1))
        fi
    fi
done

echo ""
if [ $found_issues -eq 0 ]; then
    echo "✓ All verifications passed!"
    exit 0
else
    echo "✗ Found $found_issues verification issues"
    exit 1
fi
