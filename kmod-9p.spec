# kmod RPM spec file for 9p filesystem module
# Builds for all available kernel-devel versions

%define kmod_name 9p
%define kmod_driver_version 1.0
%define kmod_rpm_release 1

# Disable debug package generation
%global debug_package %{nil}

Name:           kmod-%{kmod_name}
Version:        %{kmod_driver_version}
Release:        %{kmod_rpm_release}%{?dist}
Summary:        9P filesystem kernel module
Group:          System Environment/Kernel
License:        GPLv3
URL:            https://github.com/redbeam/v9fs-vsock
Source0:        v9fs-vsock-%{version}.tar.gz

BuildRequires:  redhat-rpm-config

# Build for multiple kernel versions - manually update this list
%if 0%{?fedora} == 44
# BuildRequires:  kernel-devel = 6.19.10-300.fc44
BuildRequires:  kernel-devel = 7.0.10-200.fc44
%endif

%if 0%{?fedora} == 43
# BuildRequires:  kernel-devel = 6.17.1-300.fc43
BuildRequires:  kernel-devel = 7.0.10-100.fc43
%endif

%if 0%{?rhel} == 10
BuildRequires:  kernel-devel = 6.12.0-227.el10
%endif

%if 0%{?rhel} >= 8
BuildRequires:  elfutils-libelf-devel
%endif

# Require at least one kernel-specific subpackage
Requires:       kmod-%{kmod_name}-module

%description
This is a meta-package that automatically installs the 9P filesystem kernel
module matching your currently installed kernel.

The 9P filesystem (Plan 9 Filesystem Protocol) allows mounting remote
filesystems using the Plan 9 protocol. This module provides the VFS
layer that integrates with the Linux kernel filesystem infrastructure.

Requires the 9pnet core module and a transport module (like 9pnet_fd)
to function.

Usage:
  mount -t 9p -o trans=fd,rfdno=<rfd>,wfdno=<wfd> <tag> <mountpoint>
  mount -t 9p -o trans=tcp <address> <mountpoint>
  mount -t 9p -o trans=vsock <CID> <mountpoint>

Install this package to get the appropriate kernel module for your system.

# Generate subpackages for each kernel version found in /usr/src/kernels/
%{expand:%(
for kver in $(ls /usr/src/kernels/ 2>/dev/null | grep -v '^\\.'); do
  # Strip dist tag and arch from kernel version for package naming
  # e.g., 7.0.9-204.fc44.x86_64 -> 7.0.9-204
  kver_short=$(echo "$kver" | sed 's/\.[^.]*\.[^.]*$//')
  cat <<EOF

%%package -n kmod-%{kmod_name}-${kver_short}
Summary: %{summary} for kernel ${kver}
Group: System Environment/Kernel
Provides: kmod-%{kmod_name} = %{?epoch:%{epoch}:}%{version}-%{release}
Provides: kmod-%{kmod_name}-module = %{?epoch:%{epoch}:}%{version}-%{release}
Requires: kernel-core = ${kver}
Requires: kmod-9pnet
Requires(post): /usr/sbin/depmod
Requires(postun): /usr/sbin/depmod
Supplements: (kmod-%{kmod_name} and kernel-core = ${kver})

%%description -n kmod-%{kmod_name}-${kver_short}
This package provides the %{kmod_name} kernel module built for kernel ${kver}.

%%post -n kmod-%{kmod_name}-${kver_short}
/sbin/depmod -a ${kver} > /dev/null 2>&1 || :

%%postun -n kmod-%{kmod_name}-${kver_short}
/sbin/depmod -a ${kver} > /dev/null 2>&1 || :

%%files -n kmod-%{kmod_name}-${kver_short}
%%defattr(-,root,root,-)
/lib/modules/${kver}/extra/%{kmod_name}/

EOF
done
)}

%prep
%setup -q -n v9fs-vsock-%{version}

# Choose the correct source directory based on distro
%if 0%{?fedora}
echo "Fedora build - using linux/ sources"
srcdir=linux
%else
echo "RHEL/EL build - using rhel/ sources"
srcdir=rhel
%endif

# Create build directories for each kernel version
for kver in $(ls /usr/src/kernels/ 2>/dev/null | grep -v '^\\.'); do
    echo "Preparing build directory for kernel ${kver}"
    mkdir -p "_kmod_build_${kver}"
    cp -r $srcdir/fs "_kmod_build_${kver}/"
done

%build
echo "=========================================="
echo "Building for multiple kernel versions"
echo "=========================================="
echo "Detected kernel versions:"
ls /usr/src/kernels/ 2>/dev/null | grep -v '^\.' | while read kver; do echo "  - $kver"; done
echo "=========================================="

# Choose the correct source directory based on distro
%if 0%{?fedora}
srcdir=linux
%else
srcdir=rhel
%endif

for kver in $(ls /usr/src/kernels/ 2>/dev/null | grep -v '^\\.'); do
    kmod_kernel_dir="/usr/src/kernels/${kver}"

    echo "Building for kernel: ${kver}"

    %{__make} %{?_smp_mflags} -C "$kmod_kernel_dir" \
        M="${PWD}/_kmod_build_${kver}/fs/9p" \
        CONFIG_9P_FS=m \
        KBUILD_MODPOST_WARN=1 \
        modules
done

echo "=========================================="

%install
# Choose the correct source directory based on distro
%if 0%{?fedora}
srcdir=linux
%else
srcdir=rhel
%endif

for kver in $(ls /usr/src/kernels/ 2>/dev/null | grep -v '^\\.'); do
    kmod_kernel_dir="/usr/src/kernels/${kver}"

    echo "Installing modules for kernel: ${kver}"

    %{__make} -C "$kmod_kernel_dir" \
        M="${PWD}/_kmod_build_${kver}/fs/9p" \
        INSTALL_MOD_PATH=%{buildroot} \
        INSTALL_MOD_DIR=extra/%{kmod_name} \
        CONFIG_9P_FS=m \
        KBUILD_MODPOST_WARN=1 \
        modules_install

    # Remove unwanted files
    find %{buildroot} -name "*.cmd" -delete
    find %{buildroot} -name ".*.d" -delete
    rm -f %{buildroot}/lib/modules/${kver}/modules.*

    # Sign modules if signing is configured
    %if 0%{?rhel} >= 8
    for module in $(find %{buildroot}/lib/modules/${kver} -type f -name \*.ko 2>/dev/null); do
        %{__strip} --strip-debug "$module"
    done
    %endif
done

%clean
rm -rf %{buildroot}

%files
%defattr(-,root,root,-)
%doc README.md
%license LICENSE

%changelog
* Tue May 26 2026 Matus Skvarla <mskvarla@redhat.com> - 1.0-1
- Modified to build for all available kernel-devel versions
- Creates separate subpackage for each kernel version
- Initial kmod package for 9P filesystem module
- Provides VFS layer for 9P filesystem
- Enables mounting remote filesystems via Plan 9 protocol
