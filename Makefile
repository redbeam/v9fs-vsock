# Makefile for v9fs-vsock kernel modules
# Choose target: 'linux' or 'rhel'

KDIR ?= /lib/modules/$(shell uname -r)/build
PWD := $(shell pwd)

.PHONY: default linux rhel linux-9pnet_fd linux-9p rhel-9pnet_fd rhel-9p clean

# Default target
default:
	@echo "Please specify a target:"
	@echo "  make linux       - Build both modules for Fedora/upstream kernel"
	@echo "  make rhel        - Build both modules for RHEL kernel"
	@echo "  make linux-9pnet_fd  - Build only transport module for Fedora"
	@echo "  make linux-9p        - Build only filesystem module for Fedora"
	@echo "  make rhel-9pnet_fd   - Build only transport module for RHEL"
	@echo "  make rhel-9p         - Build only filesystem module for RHEL"
	@echo "  make clean       - Clean all build artifacts"

# Linux targets
linux: linux-9pnet_fd linux-9p

linux-9pnet_fd:
	@echo "Building 9pnet_fd transport module (linux) with vsock support"
	$(MAKE) -C $(KDIR) M=$(PWD)/linux/net/9p \
		CONFIG_NET_9P=m CONFIG_NET_9P_FD=m \
		modules

linux-9p:
	@echo "Building 9p filesystem module (linux)"
	$(MAKE) -C $(KDIR) M=$(PWD)/linux/fs/9p \
		CONFIG_9P_FS=m KBUILD_MODPOST_WARN=1 \
		modules

# RHEL targets
rhel: rhel-9pnet_fd rhel-9p

rhel-9pnet_fd:
	@echo "Building 9pnet_fd transport module (rhel) with vsock support"
	$(MAKE) -C $(KDIR) M=$(PWD)/rhel/net/9p \
		CONFIG_NET_9P=m CONFIG_NET_9P_FD=m \
		modules

rhel-9p:
	@echo "Building 9p filesystem module (rhel)"
	$(MAKE) -C $(KDIR) M=$(PWD)/rhel/fs/9p \
		CONFIG_9P_FS=m KBUILD_MODPOST_WARN=1 \
		modules

# Clean
clean:
	@echo "Cleaning build artifacts..."
	-$(MAKE) -C $(KDIR) M=$(PWD)/linux/net/9p clean 2>/dev/null || true
	-$(MAKE) -C $(KDIR) M=$(PWD)/linux/fs/9p clean 2>/dev/null || true
	-$(MAKE) -C $(KDIR) M=$(PWD)/rhel/net/9p clean 2>/dev/null || true
	-$(MAKE) -C $(KDIR) M=$(PWD)/rhel/fs/9p clean 2>/dev/null || true
