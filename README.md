# v9fs-vsock - 9P Filesystem with VSOCK Transport Support

Kernel modules for 9P (Plan 9 Filesystem Protocol) with added VSOCK transport support for efficient VM-to-host communication.

## Packages

### kmod-9pnet_fd-vsock
Transport module providing:
- Standard fd transport (rfdno/wfdno)
- TCP transport  
- **VSOCK transport** (new) - for VM sockets communication

This package provides the `kmod-9pnet` virtual package.

### kmod-9p
The 9P filesystem VFS layer. Requires a transport module (`kmod-9pnet` provider) to function.

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

# Install both modules
dnf install kmod-9pnet_fd-vsock kmod-9p
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

GPLv2 - See LICENSE file
