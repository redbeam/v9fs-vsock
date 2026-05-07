#!/bin/bash
# Apply or reverse 9P vsock transport patches to Linux kernel source
#
# Target: Upstream Linux 7.0.0
# Date: 2026-04-21
# Based on: RHEL 6.12.0 implementation adapted for upstream
#
# Usage: ./apply-patches.sh [-r|--reverse] [kernel-source-dir]
#   -r, --reverse        Reverse/unapply the patches
#   kernel-source-dir    Target directory (default: current directory)
#
# Examples:
#   ./apply-patches.sh                    # Apply patches to current directory
#   ./apply-patches.sh /path/to/kernel    # Apply patches to specified directory
#   ./apply-patches.sh -r                 # Reverse patches in current directory
#   ./apply-patches.sh --reverse ~/linux  # Reverse patches in ~/linux

set -e

# Parse arguments
REVERSE=false
KERNEL_DIR="."

while [[ $# -gt 0 ]]; do
    case $1 in
        -r|--reverse)
            REVERSE=true
            shift
            ;;
        -h|--help)
            echo "Usage: $0 [-r|--reverse] [kernel-source-dir]"
            echo ""
            echo "Options:"
            echo "  -r, --reverse        Reverse/unapply the patches"
            echo "  -h, --help           Show this help message"
            echo ""
            echo "Arguments:"
            echo "  kernel-source-dir    Target directory (default: current directory)"
            exit 0
            ;;
        *)
            KERNEL_DIR="$1"
            shift
            ;;
    esac
done

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

if [ "$REVERSE" = true ]; then
    ACTION="Reversal"
    ACTION_VERB="Reversing"
    ACTION_PAST="reversed"
else
    ACTION="Application"
    ACTION_VERB="Applying"
    ACTION_PAST="applied"
fi

echo "==================================================================="
echo "9P vsock Transport Patch $ACTION - Upstream Linux 7.0"
echo "==================================================================="
echo ""
echo "Target kernel directory: $KERNEL_DIR"
echo "Patch directory: $SCRIPT_DIR"
echo "Mode: $ACTION_VERB patches"
echo ""

# Check if we're in a kernel source tree
if [ ! -f "$KERNEL_DIR/MAINTAINERS" ] || [ ! -d "$KERNEL_DIR/net/9p" ]; then
    echo "ERROR: $KERNEL_DIR does not appear to be a Linux kernel source tree"
    echo "       (missing MAINTAINERS file or net/9p directory)"
    exit 1
fi

# Check kernel version
if [ -f "$KERNEL_DIR/Makefile" ]; then
    VERSION=$(grep "^VERSION = " "$KERNEL_DIR/Makefile" | awk '{print $3}')
    PATCHLEVEL=$(grep "^PATCHLEVEL = " "$KERNEL_DIR/Makefile" | awk '{print $3}')
    echo "Detected kernel version: $VERSION.$PATCHLEVEL"
    echo ""

    if [ "$VERSION" -lt 6 ]; then
        echo "WARNING: These patches are designed for kernel 7.0+"
        echo "         Kernel $VERSION.$PATCHLEVEL may require adaptations"
        echo ""
        read -p "Continue anyway? (y/N) " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            exit 1
        fi
    fi
fi

cd "$KERNEL_DIR"

# Set patch flags based on mode
# --backup: Always create .orig backup files
if [ "$REVERSE" = true ]; then
    PATCH_FLAGS="-p1 -R --backup"
else
    PATCH_FLAGS="-p1 --backup"
fi

echo "$ACTION_VERB patches..."
echo ""

# Track failed patches
FAILED_PATCHES=()

# Function to apply/reverse a patch
apply_patch() {
    local step=$1
    local description=$2
    local patch_file=$3

    echo "[$step] $ACTION_VERB $description patch..."
    if patch $PATCH_FLAGS --dry-run < "$patch_file" > /dev/null 2>&1; then
        patch $PATCH_FLAGS < "$patch_file"
        echo "      ✓ Success"
    else
        echo ""
        if [ "$REVERSE" = true ]; then
            echo "ERROR: Failed to reverse $description patch (not applied or conflicts)"
        else
            echo "ERROR: Failed to apply $description patch (already applied or conflicts)"
        fi
        echo "       Debug: patch $PATCH_FLAGS --dry-run < $patch_file"
        echo ""

        # Ask user if they want to continue
        read -p "Skip this patch and continue with remaining patches? (y/N) " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            echo "Skipping $description patch..."
            FAILED_PATCHES+=("$description")
        else
            echo "Aborting patch $ACTION."
            exit 1
        fi
    fi
}

# Apply/reverse patches in appropriate order
if [ "$REVERSE" = true ]; then
    # Reverse in opposite order (3, 2, 1)
    apply_patch "1/3" "net/9p/trans_fd.c" "$SCRIPT_DIR/0003-net-9p-trans_fd.c.patch"
    apply_patch "2/3" "include/net/9p/client.h" "$SCRIPT_DIR/0002-include-net-9p-client.h.patch"
    apply_patch "3/3" "net/9p/Kconfig" "$SCRIPT_DIR/0001-net-9p-Kconfig.patch"
else
    # Apply in normal order (1, 2, 3)
    apply_patch "1/3" "net/9p/Kconfig" "$SCRIPT_DIR/0001-net-9p-Kconfig.patch"
    apply_patch "2/3" "include/net/9p/client.h" "$SCRIPT_DIR/0002-include-net-9p-client.h.patch"
    apply_patch "3/3" "net/9p/trans_fd.c" "$SCRIPT_DIR/0003-net-9p-trans_fd.c.patch"
fi

echo ""
echo "==================================================================="
if [ ${#FAILED_PATCHES[@]} -eq 0 ]; then
    echo "All patches $ACTION_PAST successfully!"
else
    echo "Patch $ACTION completed with errors"
    echo "==================================================================="
    echo ""
    echo "WARNING: The following patches failed:"
    for failed in "${FAILED_PATCHES[@]}"; do
        echo "  ✗ $failed"
    done
    echo ""
    echo "Successfully $ACTION_PAST patches:"
    if [ "$REVERSE" = true ]; then
        # In reverse mode, check which ones succeeded
        [[ ! " ${FAILED_PATCHES[@]} " =~ " net/9p/trans_fd.c " ]] && echo "  ✓ net/9p/trans_fd.c"
        [[ ! " ${FAILED_PATCHES[@]} " =~ " include/net/9p/client.h " ]] && echo "  ✓ include/net/9p/client.h"
        [[ ! " ${FAILED_PATCHES[@]} " =~ " net/9p/Kconfig " ]] && echo "  ✓ net/9p/Kconfig"
    else
        # In apply mode, check which ones succeeded
        [[ ! " ${FAILED_PATCHES[@]} " =~ " net/9p/Kconfig " ]] && echo "  ✓ net/9p/Kconfig"
        [[ ! " ${FAILED_PATCHES[@]} " =~ " include/net/9p/client.h " ]] && echo "  ✓ include/net/9p/client.h"
        [[ ! " ${FAILED_PATCHES[@]} " =~ " net/9p/trans_fd.c " ]] && echo "  ✓ net/9p/trans_fd.c"
    fi
fi
echo "==================================================================="
echo ""

if [ "$REVERSE" = true ]; then
    echo "Patches have been reversed."
    echo ""
    echo "The following files have been restored to their original state:"
    echo "  - net/9p/Kconfig"
    echo "  - include/net/9p/client.h"
    echo "  - net/9p/trans_fd.c"
    echo ""
    echo "Backup files (.orig) have been created with the previous patched versions."
    echo ""
    echo "Next steps:"
    echo ""
    echo "1. Make any needed changes to the patch files in:"
    echo "   $SCRIPT_DIR"
    echo ""
    echo "2. Reapply the patches:"
    echo "   $0"
    echo ""
    echo "3. Clean up backup files when done (optional):"
    echo "   find . -name '*.orig' -type f -delete"
    echo ""
else
    echo "Backup files (.orig) have been created with the original versions."
    echo ""
    echo "Next steps:"
    echo ""
    echo "1. Configure the kernel:"
    echo "   make menuconfig"
    echo "   Navigate to: Networking support -> Plan 9 Resource Sharing Support"
    echo "   Enable: [M] 9P VSOCK Transport"
    echo ""
    echo "   Or edit .config directly:"
    echo "   CONFIG_VSOCKETS=y"
    echo "   CONFIG_NET_9P=m"
    echo "   CONFIG_NET_9P_FD=m"
    echo "   CONFIG_NET_9P_VSOCK=y"
    echo ""
    echo "2. Build the modules:"
    echo "   make M=net/9p modules"
    echo ""
    echo "3. Install the modules:"
    echo "   sudo make M=net/9p modules_install"
    echo "   sudo depmod -a"
    echo ""
    echo "4. Load the modules:"
    echo "   sudo modprobe 9pnet"
    echo "   sudo modprobe 9pnet_fd"
    echo ""
    echo "5. Verify vsock transport is available:"
    echo "   modinfo 9pnet_fd | grep vsock"
    echo "   Expected output: alias: 9p-vsock"
    echo ""
    echo "6. Mount using vsock:"
    echo "   mount -t 9p -o trans=vsock <CID> /mnt/point"
    echo ""
    echo "   Examples:"
    echo "   - From guest, mount host: mount -t 9p -o trans=vsock 2 /mnt/host"
    echo "   - From host, mount guest:  mount -t 9p -o trans=vsock 3 /mnt/guest"
    echo ""
    echo "7. Clean up backup files when satisfied (optional):"
    echo "   find net/9p include/net/9p -name '*.orig' -type f -delete"
    echo ""
    echo "See README.md and CLAUDE.md for complete documentation."
fi
echo ""

# Exit with appropriate code
if [ ${#FAILED_PATCHES[@]} -gt 0 ]; then
    exit 1
fi
exit 0
