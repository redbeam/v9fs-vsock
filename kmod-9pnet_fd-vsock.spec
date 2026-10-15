# kmod RPM spec file for 9P transport module with vsock support

%define kmod_name 9pnet_fd-vsock
%define kmod_driver_version 1.0
%define kmod_rpm_release 1

# Kernel headers are bundled in the source tarball
# Will auto-detect all bundled kernels during build

# Disable debug package generation
%global debug_package %{nil}

Name:           kmod-%{kmod_name}
Version:        %{kmod_driver_version}
Release:        %{kmod_rpm_release}%{?dist}
Summary:        9P transport kernel module with vsock support
Group:          System Environment/Kernel
License:        GPLv3
URL:            https://github.com/redbeam/v9fs-vsock
Source0:        v9fs-vsock-%{version}.tar.gz
Source1:        kernel-versions.txt
Source2:        bundled-kernels.tar.gz

# Kernel headers are bundled in the source tarball - no kernel-devel needed!
BuildRequires:  redhat-rpm-config
BuildRequires:  make
BuildRequires:  gcc
%if 0%{?rhel} >= 8
BuildRequires:  elfutils-libelf-devel
%endif

# Meta-package requires kernel-specific subpackage
Requires:       kmod-%{kmod_name}-module

%description
This is a meta-package that automatically installs the 9P transport kernel
module matching your currently installed kernel.

The 9P transport module provides vsock support, enabling mounting 9P filesystems
over VM sockets (vsock) for efficient communication between virtual machines and
their hosts, or between containers and hosts.

Mount syntax: mount -t 9p -o trans=vsock <CID> /mnt/point

Install this package to get the appropriate kernel module for your system.

# Generate kernel-specific subpackages for all bundled kernels
# This runs during spec parse time, reading from kernel-versions.txt
%{expand:%(
if [ -f "%{_sourcedir}/kernel-versions.txt" ]; then
  for kver in $(cat %{_sourcedir}/kernel-versions.txt | grep -v '^\.' ); do
    # Strip distribution tag and arch from kernel version for package naming
    # e.g. 6.12.0-211.29.1.el10_2.x86_64 -> 6.12.0-211.29.1
    kver_short=$(echo "$kver" | sed 's/\.el[0-9_]*\..*$//')
    cat <<EOF

%%package -n kmod-%{kmod_name}-${kver_short}
Summary: %{summary} for kernel ${kver}
Group: System Environment/Kernel
Provides: kmod-%{kmod_name} = %{?epoch:%{epoch}:}%{version}-%{release}
Provides: kmod-%{kmod_name}-module = %{?epoch:%{epoch}:}%{version}-%{release}
Provides: kmod-9pnet = %{?epoch:%{epoch}:}%{version}-%{release}
Requires: kernel-core-${kver}
Requires(post): /usr/sbin/depmod
Requires(postun): /usr/sbin/depmod
Supplements: (kmod-%{kmod_name} and kernel-core-${kver})

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
fi
)}

%prep
%setup -q -n v9fs-vsock-%{version}
# Extract bundled kernel headers
tar xzf %{SOURCE2}

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
        M="${PWD}/$srcdir/net/9p" \
        clean || :

    # Build the module
    %{__make} %{?_smp_mflags} -C "$kmod_kernel_dir" \
        M="${PWD}/$srcdir/net/9p" \
        CONFIG_NET_9P=m \
        CONFIG_NET_9P_FD=m \
        modules

    # Save the built module to a temporary location
    mkdir -p "${PWD}/built-modules/${kver}"
    cp -f "$srcdir/net/9p/"*.ko "${PWD}/built-modules/${kver}/"
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
- Initial kmod package for 9P vsock transport
- Adds vsock transport support to 9pnet_fd module
- Enables mounting 9P filesystems over VM sockets
