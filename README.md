# v9fs-vsock - 9P Filesystem with VSOCK Transport Support

Kernel modules for 9P (Plan 9 Filesystem Protocol) with added VSOCK transport support for efficient VM-to-host communication.

## Packages

Each module is shipped as one metapackage plus one subpackage per kernel it was
built for, e.g. `kmod-9p` and `kmod-9p-6.12.0-211.29.1`. Installing the
metapackage pulls in the subpackages for all installed kernels it has a build
for; it never installs or upgrades a kernel. Installing a matching kernel later
pulls in its subpackage automatically.

The metapackage itself carries no kernel list. Each subpackage declares
`Supplements: (kmod-9p and kernel-core-uname-r = <kernel>)`, so subpackages
from separate builds (e.g. a daily build for the newest kernel and a bundled
build for older ones) can be published side by side in one repository.

### kmod-9pnet_fd-vsock
Transport module providing:
- Standard fd transport (rfdno/wfdno)
- TCP transport  
- **VSOCK transport** (new) - for VM sockets communication

### kmod-9p
The 9P filesystem VFS layer. Each `kmod-9p-<kernel>` subpackage requires the
`kmod-9pnet_fd-vsock-<kernel>` subpackage built for the same kernel.

## Packaging Branches

This branch contains only the module sources and tooling. The RPM specfiles
live in separate branches:

| Branch | Builds for |
|---|---|
| `singlebuild` | The newest kernel-devel available at build time |
| `multibuild` | Every kernel source tree present in `/usr/src/kernels` at build time |
| `multibuild-bundled-kernels` | Every kernel in `bundled-kernels.tar` (uncompressed, laid out as `bundled-kernels/<kernel>/`, not stored in the repository) |

## Usage

### Mount using VSOCK (VM socket)
```bash
# Mount from a VM to host (CID 2) or another VM
mount -t 9p -o trans=vsock,port=564 2 /mnt/shared
```

### Mount using TCP
```bash
mount -t 9p -o trans=tcp 192.168.1.100 /mnt/shared
```

### Mount using file descriptors
```bash
mount -t 9p -o trans=fd,rfdno=3,wfdno=4 mytag /mnt/shared
```

## Installation

### From COPR
```bash
# Enable the COPR repository
dnf copr enable <your-username>/v9fs-vsock

# Install both modules (kmod-9p pulls in the matching transport module)
dnf install kmod-9p
```

If the installed kernel has no matching build, only the metapackage is
installed and no module is provided for that kernel.

Subpackages are pulled in as weak dependencies. If `install_weak_deps=False`
is set in `/etc/dnf/dnf.conf`, install the subpackage for the running kernel
explicitly:
```bash
dnf install "kmod-9p-$(uname -r | sed 's/\.[^.]*\.[^.]*$//')"
```

## Building from Source

The modules are built using the kernel module build infrastructure:

```bash
# Build for current kernel
make -C /lib/modules/$(uname -r)/build M=$(pwd)/net modules
make -C /lib/modules/$(uname -r)/build M=$(pwd)/fs modules

# Install
make -C /lib/modules/$(uname -r)/build M=$(pwd)/net modules_install
make -C /lib/modules/$(uname -r)/build M=$(pwd)/fs modules_install
depmod -a
```

## Source Versions

- `linux/` - Modified sources for Fedora (latest kernel)
- `rhel/` - Modified sources for RHEL/CentOS kernels

## License

GPLv3 - See LICENSE file
