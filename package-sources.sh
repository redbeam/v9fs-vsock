#!/bin/bash
# Script to package v9fs-vsock sources into tarball
# Creates a single source tarball used by both kmod packages

set -e

VERSION="1.0"
OUTDIR="."
PACKAGE_NAME="v9fs-vsock"

echo "=== Packaging v9fs-vsock sources ==="

# Create staging directory
STAGEDIR="$OUTDIR/$PACKAGE_NAME-$VERSION"
mkdir -p "$STAGEDIR"

# Copy sources
echo "Copying sources..."
cp -r linux "$STAGEDIR/"
cp -r rhel "$STAGEDIR/"
cp README.md LICENSE "$STAGEDIR/" 2>/dev/null || true

# Create tarball
echo "Creating tarball..."
(cd "$OUTDIR" && tar czf "$PACKAGE_NAME-$VERSION.tar.gz" "$PACKAGE_NAME-$VERSION/")

# Cleanup staging directory
rm -rf "$STAGEDIR"

echo ""
echo "=== Summary ==="
echo "Created: $OUTDIR/$PACKAGE_NAME-$VERSION.tar.gz"
ls -lh "$OUTDIR/$PACKAGE_NAME-$VERSION.tar.gz"
echo ""
echo "This tarball is used by both:"
echo "  - kmod-9pnet_fd-vsock.spec"
echo "  - kmod-9p.spec"
echo ""
echo "To build SRPMs locally:"
echo "  rpmbuild -bs kmod-9pnet_fd-vsock.spec --define \"_sourcedir $PWD\" --define \"_srcrpmdir $PWD\""
echo "  rpmbuild -bs kmod-9p.spec --define \"_sourcedir $PWD\" --define \"_srcrpmdir $PWD\""
