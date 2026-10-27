# kmod RPM spec file for 9p filesystem module

%define kmod_name 9p
%define kmod_driver_version 1.0
%define kmod_rpm_release 1

# Builds for every kernel in bundled-kernels.tar (Source1)

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
Source1:        bundled-kernels.tar

# Kept uncompressed so listing it at parse time can seek past file contents;
# %%global evaluates the listing only once per parse
%global bundled_kvers %(echo $(tar tf %{_sourcedir}/bundled-kernels.tar 2>/dev/null | awk -F/ '$1 == "bundled-kernels" && $2 != "" {print $2}' | sort -u))

# Kernel headers come from bundled-kernels.tar - no kernel-devel needed
BuildRequires:  redhat-rpm-config
BuildRequires:  make
BuildRequires:  gcc
%if 0%{?rhel} >= 8
BuildRequires:  elfutils-libelf-devel
%endif

# Module subpackages pull themselves in via Supplements, so this package
# carries no kernel list and builds for different kernels can coexist

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

# Generate kernel-specific subpackages for all bundled kernels
%{expand:%(
  for kver in %{bundled_kvers}; do
    # Strip distribution tag and arch from kernel version for package naming
    # e.g. 6.12.0-211.29.1.el10_2.x86_64 -> 6.12.0-211.29.1
    #      7.0.10-201.fc44.x86_64        -> 7.0.10-201
    kver_short=$(echo "$kver" | sed 's/\.[^.]*\.[^.]*$//')
    cat <<EOF

%%package -n kmod-%{kmod_name}-${kver_short}
Summary: %{summary} for kernel ${kver}
Group: System Environment/Kernel
Requires: kmod-9pnet_fd-vsock-${kver_short}
Supplements: (kmod-%{kmod_name} and kernel-core-uname-r = ${kver})
Requires(post): /usr/sbin/depmod
Requires(postun): /usr/sbin/depmod

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
# Extract bundled kernel headers
tar xf %{SOURCE1}

%build
# Choose the correct source directory based on distro
%if 0%{?fedora}
echo "Fedora build - using linux/ sources"
srcdir=linux
%else
echo "RHEL/EL build - using rhel/ sources"
srcdir=rhel
%endif

# Build the module for all bundled kernels
for kver in $(ls bundled-kernels/ 2>/dev/null | grep -v '^\.' ); do
    kmod_kernel_dir="${PWD}/bundled-kernels/${kver}"

    echo "Building for kernel: ${kver}"
    echo "Kernel headers at: ${kmod_kernel_dir}"

    # Clean previous build artifacts
    %{__make} -C "$kmod_kernel_dir" \
        M="${PWD}/$srcdir/fs/9p" \
        clean || :

    # Build the module (allow undefined symbols - they come from kmod-9pnet)
    %{__make} %{?_smp_mflags} -C "$kmod_kernel_dir" \
        M="${PWD}/$srcdir/fs/9p" \
        CONFIG_9P_FS=m \
        KBUILD_MODPOST_WARN=1 \
        modules

    # Save the built module to a temporary location
    mkdir -p "${PWD}/built-modules/${kver}"
    cp -f "$srcdir/fs/9p/"*.ko "${PWD}/built-modules/${kver}/"
done

%install
# Install modules for all bundled kernels
for kver in $(ls bundled-kernels/ 2>/dev/null | grep -v '^\.' ); do
    echo "Installing modules for kernel: ${kver}"

    # Create module directory
    mkdir -p "%{buildroot}/lib/modules/${kver}/extra/%{kmod_name}"

    # Copy the built modules from our temporary location
    cp -f "${PWD}/built-modules/${kver}/"*.ko \
        "%{buildroot}/lib/modules/${kver}/extra/%{kmod_name}/"

    # Sign modules if signing is configured
    %if 0%{?rhel} >= 8
    for module in $(find %{buildroot}/lib/modules/${kver} -type f -name \*.ko 2>/dev/null); do
        %{__strip} --strip-debug "$module"
    done
    %endif
done

# Remove unwanted files
find %{buildroot} -name "*.cmd" -delete
find %{buildroot} -name ".*.d" -delete
find %{buildroot}/lib/modules -name "modules.*" -delete 2>/dev/null || :

%clean
rm -rf %{buildroot}

%files
%defattr(-,root,root,-)
%doc README.md
%license LICENSE

%changelog
* Thu May 7 2026 Matus Skvarla <mskvarla@redhat.com> - 1.0-1
- Initial kmod package for 9P filesystem module
- Provides VFS layer for 9P filesystem
- Enables mounting remote filesystems via Plan 9 protocol
