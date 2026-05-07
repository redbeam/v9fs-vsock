# kmod RPM spec file for 9P transport module with vsock support

%define kmod_name 9pnet_fd-vsock
%define kmod_driver_version 1.0
%define kmod_rpm_release 1

# Kernel version to build for (can be overridden with --define "kernel_version X.Y.Z")
%{!?kernel_version: %define kernel_version 7.0.9-204%{?dist}}

# Full kernel version including the architecture for use in file system paths
%define kernel_version_full %{kernel_version}.%{_arch}

# Disable debug package generation
%global debug_package %{nil}

Name:           kmod-%{kmod_name}-%{kernel_version}
Version:        %{kmod_driver_version}
Release:        %{kmod_rpm_release}%{?dist}
Summary:        9P transport kernel module with vsock support
Group:          System Environment/Kernel
License:        GPLv3
URL:            https://github.com/redbeam/v9fs-vsock
Source0:        v9fs-vsock-%{version}.tar.gz

BuildRequires:  kernel-devel = %{kernel_version}
Requires:       kernel = %{kernel_version}
Provides:       kmod-%{kmod_name}-%{kver} = %{kernel_version}

BuildRequires:  redhat-rpm-config
%if 0%{?rhel} >= 8
BuildRequires:  elfutils-libelf-devel
%endif

Requires(post):   /usr/sbin/depmod
Requires(postun): /usr/sbin/depmod

Provides:       kmod-%{kmod_name} = %{?epoch:%{epoch}:}%{version}-%{release}
Provides:       kmod-9pnet = %{?epoch:%{epoch}:}%{version}-%{release}

%description
This package provides the 9P transport kernel module with added vsock support.
It enables mounting 9P filesystems over VM sockets (vsock) for efficient
communication between virtual machines and their hosts, or between containers
and hosts.

Mount syntax: mount -t 9p -o trans=vsock <CID> /mnt/point

%prep
%setup -q -n v9fs-vsock-%{version}

%build
kmod_kernel_dir=/usr/src/kernels/%{kernel_version_full}
echo "Building against kernel headers at: $kmod_kernel_dir"

# Choose the correct source directory based on distro
%if 0%{?fedora}
echo "Fedora build - using linux/ sources"
srcdir=linux
%else
echo "RHEL/EL build - using rhel/ sources"
srcdir=rhel
%endif

# Build the module
%{__make} %{?_smp_mflags} -C $kmod_kernel_dir M=%{_builddir}/v9fs-vsock-%{version}/$srcdir/net/9p \
    CONFIG_NET_9P=m \
    CONFIG_NET_9P_FD=m \
    CONFIG_NET_9P_VSOCK=y \
    modules

%install
kmod_kernel_dir=/usr/src/kernels/%{kernel_version_full}

# Choose the correct source directory based on distro
%if 0%{?fedora}
srcdir=linux
%else
srcdir=rhel
%endif

# Install the module
%{__make} -C $kmod_kernel_dir M=%{_builddir}/v9fs-vsock-%{version}/$srcdir/net/9p \
    INSTALL_MOD_PATH=%{buildroot} \
    INSTALL_MOD_DIR=extra/%{kmod_name} \
    CONFIG_NET_9P=m \
    CONFIG_NET_9P_FD=m \
    CONFIG_NET_9P_VSOCK=y \
    modules_install

# Remove unwanted files
find %{buildroot} -name "*.cmd" -delete
find %{buildroot} -name ".*.d" -delete
rm -f %{buildroot}/lib/modules/%{kernel_version_full}/modules.*

# Sign modules if signing is configured
%if 0%{?rhel} >= 8
for module in $(find %{buildroot} -type f -name \*.ko); do
    %{__strip} --strip-debug "$module"
done
%endif

%clean
rm -rf %{buildroot}

%post
/sbin/depmod -a > /dev/null 2>&1 || :

%postun
/sbin/depmod -a > /dev/null 2>&1 || :

%files
%defattr(-,root,root,-)
%doc README.md
%license LICENSE
/lib/modules/*/extra/%{kmod_name}/

%changelog
* Thu May 7 2026 Matus Skvarla <mskvarla@redhat.com> - 1.0-1
- Initial kmod package for 9P vsock transport
- Adds vsock transport support to 9pnet_fd module
- Enables mounting 9P filesystems over VM sockets
