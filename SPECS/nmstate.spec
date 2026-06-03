%?python_enable_dependency_generator
%define srcname nmstate
%define libname libnmstate

Name:           nmstate
Version:        2.2.60
Release:        1%{?dist}
Summary:        Declarative network manager API
License:        LGPLv2+
URL:            https://github.com/%{srcname}/%{srcname}
Source0:        https://github.com/nmstate/nmstate/releases/download/v%{version}/nmstate-%{version}.tar.gz
Source1:        https://github.com/nmstate/nmstate/releases/download/v%{version}/nmstate-%{version}.tar.gz.asc
Source2:        https://nmstate.io/nmstate.gpg
Source3:        https://github.com/nmstate/nmstate/releases/download/v%{version}/nmstate-vendor-%{version}.tar.xz
Patch1:         0001-nispor-fix-ipoib-iface-type.patch
BuildRequires:  python3-devel
BuildRequires:  python3-setuptools
BuildRequires:  gnupg2
BuildRequires:  rust-toolset
BuildRequires:  pkg-config
BuildRequires:  systemd
Requires:       (nmstate-libs%{?_isa} = %{version}-%{release} if nmstate-libs)

%description
Nmstate is a library with an accompanying command line tool that manages host
networking settings in a declarative manner and aimed to satisfy enterprise
needs to manage host networking through a northbound declarative API and multi
provider support on the southbound.


%package libs
Summary:        C binding of nmstate
# Use Recommends for NetworkManager because only access to NM DBus is required,
# but NM could be running on a different host
Recommends:     NetworkManager
# Avoid automatically generated profiles
Recommends:     NetworkManager-config-server
License:        ASL 2.0

%package -n python3-%{libname}
Summary:        nmstate Python 3 API library
# Use Recommends for NetworkManager because only access to NM DBus is required,
# but NM could be running on a different host
Recommends:     NetworkManager
# Avoid automatically generated profiles
Recommends:     NetworkManager-config-server
# Use Suggests for NetworkManager-ovs and NetworkManager-team since it is only
# required for OVS and team support
Suggests:       NetworkManager-ovs
Suggests:       NetworkManager-team
# FIXME: Once upstream included nispor into requirement.txt, remove below line
Provides:       nmstate-plugin-ovsdb = %{version}-%{release}
Requires:       %{name}-libs%{?_isa} = %{version}-%{release}
Obsoletes:      nmstate-plugin-ovsdb < 2.1-1

%package devel
Summary:        C binding development files of nmstate
License:        ASL 2.0
Requires:       nmstate-libs%{?_isa} = %{?epoch:%{epoch}:}%{version}-%{release}

%package static
Summary:        Static development files for nmstate
Group:          Development/Libraries
Requires:       %{name}-devel%{?_isa} = %{version}-%{release}

%description static
Static C library bindings for nmstate.

%description libs
This package contains the C binding of nmstate.

%description devel
This package contains the C binding development files of nmstate.


%description -n python3-%{libname}
This package contains the Python 3 library for Nmstate.

%prep
gpg2 --import --import-options import-export,import-minimal %{SOURCE2} > ./gpgkey-mantainers.gpg
gpgv2 --keyring ./gpgkey-mantainers.gpg %{SOURCE1} %{SOURCE0}

%autosetup -n %{name}-%{version_no_tilde} -p1 %{?rhel:-a3}

# If we have a patch for a vendored dependency, cargo refuses to build,
# in order to prevent accidental manual changes to vendored crates.
# This is not needed in an rpm build. Clear the list of files for which
# to check the checksum.
find vendor -name .cargo-checksum.json \
  -exec sed -i.uncheck -e 's/"files":{[^}]*}/"files":{ }/' '{}' '+'

pushd rust
%if 0%{?rhel}
mv ../vendor ./
%cargo_prep -v vendor
%else
%cargo_prep
%endif
popd

%build
pushd rust/src/python
%py3_build
popd
pushd rust
%cargo_build
%cargo_license_summary
%{cargo_license} > ../LICENSE.dependencies
%if 0%{?rhel}
%cargo_vendor_manifest
%endif
popd

%install
env SKIP_PYTHON_INSTALL=1 \
    PREFIX=%{_prefix} \
    LIBDIR=%{_libdir} \
    SYSCONFDIR=%{_sysconfdir} \
    %make_install

pushd rust/src/python
%py3_install
popd


%files
%doc README.md
%license LICENSE.dependencies
%if 0%{?rhel}
%license rust/cargo-vendor.txt
%endif
%doc examples/
%{_mandir}/man8/nmstate.service.8*
%{_mandir}/man8/nmstatectl.8*
%{_mandir}/man8/nmstate-autoconf.8*
%{_bindir}/nmstatectl
%{_bindir}/nmstate-autoconf
%{_unitdir}/nmstate.service
%dir %{_sysconfdir}/%{name}
%{_sysconfdir}/%{name}/README

%files -n python3-%{libname}
%license LICENSE
%{python3_sitelib}/%{libname}
%{python3_sitelib}/%{srcname}-*.egg-info/

%files libs
%license rust/LICENSE
%{_libdir}/libnmstate.so.*

%files devel
%license LICENSE
%{_libdir}/libnmstate.so
%{_includedir}/nmstate.h
%{_libdir}/pkgconfig/nmstate.pc

%files static
%{_libdir}/libnmstate.a

%post libs
/sbin/ldconfig

%postun libs
/sbin/ldconfig

%changelog
* Thu May 06 2026 Ján Václav <jvaclav@redhat.com> - 2.2.60-1
- Upgrade to 2.2.60
- ipv4: Add new parameter prefix-route-metric RHEL-170695

* Thu Mar 05 2026 Rahul Rajesh <rrajesh@redhat.com> - 2.2.59-1
- Upgrade to 2.2.59
- Add support for lock-mtu option. RHEL-151933.

* Wed Feb 11 2026 Mingyu Shi <mshi@redhat.com> - 2.2.58-1
- Upgrade to 2.2.58
- vrf: Handle ignore interface when verifying desired state. RHEL-141606
- alt-name: Remove alt-names when interface marked as absent. RHEL-141602
- hsr: Automatically disable IP on hsr port. RHEL-141609
- hsr: add support for configuring "interlink" property. RHEL-141608
- Support referring interface name using its alternative name. RHEL-141601

* Tue Dec 09 2025 Gris Ge <fge@redhat.com> - 2.2.57-1
- Upgrade to 2.2.57
- Add libreswan leftprotoport and rightprotoport support. (RHEL-130912)

* Tue Nov 25 2025 Gris Ge <fge@redhat.com> - 2.2.56-1
- Upgrade to 2.2.56
- Allow using VRF name to specify route table. RHEL-123541
- Support OVS-DPDK dpdk-lsc-interrupt in nmstate. RHEL-125052
- Applying desired state with static DNS with static IP will touch `br-ex` even not mentioned. RHEL-126731
- Support rightca ipsec option. RHEL-123542

* Mon Oct 20 2025 Gris Ge <fge@redhat.com> - 2.2.54-1
- Upgrade to 2.2.54.
- Automatically set HSR port MAC address. RHEL-122171
- Fix OVSDB query failure on database bigger than 20KiB. RHEL-121992

* Tue Sep 16 2025 Gris Ge <fge@redhat.com> - 2.2.52-1
- Upgrade to 2.2.52
- Support interface altnative name. RHEL-110781

* Mon Sep 01 2025 Mingyu Shi <mshi@redhat.com> - 2.2.50-1
- Upgrade to 2.2.50
- Support MAC referring for VLAN in gen_conf. RHEL-110369
- Introduce state: ignore for route. RHEL-107130
- Support PCI address matching in gen_conf. RHEL-110369
- Support MacSec interface in gen_conf. RHEL-110369

* Tue Aug 5 2025 Rahul Rajesh <rrajesh@redhat.com> - 2.2.49-1
- Upgrade to 2.2.49
- Ignore desired MAC for bonds with fail_over_mac. RHEL-107526
- Fix setting DNS only with search or option. RHEL-104797

* Sat Jul 12 2025 Gris Ge <fge@redhat.com> - 2.2.48-1
- Upgrade to 2.2.48
- Validate OVN bridge mapping. RHEL-85787
- Support bond `lacp_active` and `ns_ip6_target`. RHEL-85784
- Support matching by PCI adress. RHEL-88993
- Apply dispatch changes first. RHEL-101742
- Fix SRIOV VF reference. RHEL-93180

* Fri Jun 20 2025 Gris Ge <fge@redhat.com> - 2.2.46-1
- Upgrade to 2.2.46
- Store DNS to both iface and global DNS. RHEL-91291
- Support nmpolicy against down iface. RHEL-88989
- Support removal VLAN connection with empty ifname. RHEL-93146

* Wed May 28 2025 Gris Ge <fge@redhat.com> - 2.2.45-1
- Upgrade to 2.2.25
- Fix stuck of nmstatectl show on OVS. RHEL-93176

* Fri Apr 18 2025 Gris Ge <fge@redhat.com> - 2.2.44-1
- Upgrade to 2.2.44
- Refer route next hop interface by MAC. RHEL-32495
- Support reapply on mac-ref interface. RHEL-87794

* Wed Mar 26 2025 Mingyu Shi <mshi@redhat.com> - 2.2.43-1
- Upgrade to 2.2.43
- Support for vlan-egress-priority-map configuration. RHEL-67631
- Support FEC. RHEL-80725
- Support quickack. RHEL-80418

* Wed Mar 05 2025 Gris Ge <fge@redhat.com> - 2.2.42-1
- Upgrade to 2.2.42
- Support congression windows on route. RHEL-59589

* Sun Feb 23 2025 Gris Ge <fge@redhat.com> - 2.2.41-1
- Upgrade to 2.2.41
- Fix the lose of OVS DB system-id. RHEL-78652
- Support overriding interface config. RHEL-59935

* Fri Jan 24 2025 Fernando Fernandez Mancera <ferferna@redhat.com> - 2.2.40-1
- Upgrade to 2.2.40
- Do not deactivate connection when removing routes. RHEL-70138
- Use specific libnmstate logger. RHEL-72016
- Do not deactivate connection if mptcp flags didn't change. RHEL-53211

* Mon Jan 20 2025 Gris Ge <fge@redhat.com> - 2.2.39-1
- Upgrade to 2.2.39
- Avoid unnecessary deactivation. RHEL-64707

* Thu Oct 24 2024 Gris Ge <fge@redhat.com> - 2.2.38-1
- Upgrade to 2.2.38
- Preserve current IP setting for multiconnect profile. RHEL-61890
- Fix profile name changing. RHEL-59239
- IPvlan support. RHEL-43438
- Handle ipv6.method: ignore. RHEL-58406

* Mon Oct 07 2024 Fernando Fernandez Mancera <ferferna@redhat.com> - 2.2.37-1
- Upgrade to 2.2.37
- Only search desired interface for storing route rule. RHEL-59965

* Tue Sep 24 2024 Gris Ge <fge@redhat.com> - 2.2.36-1
- Upgrade to 2.2.36
- Support route source. RHEL-56258
- Fix setting empty MPTCP flags. RHEL-38607
- Fix gc mode on blackhole route. RHEL-56727
- Support ipsec require-id-on-certificate. RHEL-50696
- Reselect iface DNS if desired. RHEL-56557

* Thu Aug 22 2024 Gris Ge <fge@redhat.com> - 2.2.35-1
- Upgrade to 2.2.35
- Fix gen_diff on VLAN ID change. RHEL-38623
- Fix Nmpolicy on mac-address identifier. RHEL-54292
- Fix reapply. RHEL-50556

* Thu Jun 13 2024 Gris Ge <fge@redhat.com> - 2.2.33-1
- Upgrade to 2.2.33
- Fix validation of controller overbook. RHEL-40683
- Support DNS and route in kernel mode. RHEL-37665

* Thu May 30 2024 Gris Ge <fge@redhat.com> - 2.2.32-1
- Upgrade to 2.2.32
- Set VLAN reorder-headers to true by default. RHEL-33362

* Mon May 20 2024 Fernando Fernandez Mancera <ferferna@redhat.com> - 2.2.31-1
- Upgrade to 2.2.31
- Support IPSec leftsubnet property. RHEL-26755

* Fri May 03 2024 Fernando Fernandez Mancera <ferferna@redhat.com> - 2.2.30-1
- Upgrade to 2.2.30

* Thu Apr 25 2024 Fernando Fernandez Mancera <ferferna@redhat.com> - 2.2.29-1
- Upgrade to 2.2.29

* Mon Apr 22 2024 Fernando Fernandez Mancera <ferferna@redhat.com> - 2.2.28-1
- Upgrade to 2.2.28

* Thu Mar 21 2024 Gris Ge <fge@redhat.com> - 2.2.27-1
### Breaking changes
 - N/A

### New features
 - Support TCP congestion window(cwnd) in route. (59f99632)
 - Support query interface driver. (67817c23)
 - New API to generate changed state. (fe5327a2)

### Bug fixes
 - Include driver information for `persist-nic-names` subcommand. (1129e46b)
 - nm: Protect global DNS config in checkpoint. (881373ba)
 - route rule: Append rule instead of overriding when iface defined. (88d3d3ef)
- Resolves RHEL-19409

* Wed Mar 13 2024 Gris Ge <fge@redhat.com> - 2.2.26-1
- Upgrade to 2.2.26

* Thu Feb 22 2024 Fernando Fernandez Mancera <ferferna@redhat.com> - 2.2.25-1
- Upgrade to 2.2.25

* Thu Feb 08 2024 Gris Ge <fge@redhat.com> - 2.2.24-1
- Upgrade to 2.2.24

* Thu Jan 18 2024 Fernando Fernandez Mancera <ferferna@redhat.com> - 2.2.23-1
- Upgrade to 2.2.23.

* Fri Jan 05 2024 Gris Ge <fge@redhat.com> - 2.2.22-1
- Upgrade to 2.2.22.

* Tue Dec 19 2023 Gris Ge <fge@redhat.com> - 2.2.21-2
- Fix `ipsec-interface` option. RHEL-17403

* Fri Dec 15 2023 Íñigo Huguet <ihuguet@redhat.com> - 2.2.21-1
- Upgrade to 2.2.21.

* Thu Nov 30 2023 Gris Ge <fge@redhat.com> - 2.2.20-1
- Upgrade to 2.2.20.

* Wed Nov 15 2023 Gris Ge <fge@redhat.com> - 2.2.19-1
- Upgrade to 2.2.19.

* Thu Nov 02 2023 Gris Ge <fge@redhat.com> - 2.2.18-1
- Upgrade to 2.2.18.

* Thu Sep 21 2023 Gris Ge <fge@redhat.com> - 2.2.16-1
- Upgrade to 2.2.16.

* Mon Sep 04 2023 Gris Ge <fge@redhat.com> - 2.2.15-3
- Rebuild for RHEL 9.4.

* Wed Aug 30 2023 Gris Ge <fge@redhat.com> - 2.2.15-2
- Rebuild for RHEL 9.3.

* Wed Aug 23 2023 Gris Ge <fge@redhat.com> - 2.2.15-1
- Upgrade to 2.2.15

* Wed Jul 26 2023 Gris Ge <fge@redhat.com> - 2.2.14-1
- Upgrade to 2.2.14

* Thu Jul 13 2023 Gris Ge <fge@redhat.com> - 2.2.13-1
- Upgrade to 2.2.13

* Wed Jun 07 2023 Gris Ge <fge@redhat.com> - 2.2.12-2
- Fix regression on SRIOV timeout. RHBZ#2212380

* Thu Jun 01 2023 Fernando Fernandez Mancera <ferferna@redhat.com> - 2.2.12-1
- Upgrade to 2.2.12

* Wed May 17 2023 Fernando Fernandez Mancera <ferferna@redhat.com> - 2.2.11-1
- Upgrade to 2.2.11

* Tue Apr 25 2023 Gris Ge <fge@redhat.com> - 2.2.10-3
- Fix error when DHCP enabled with auto ip on STP bridge

* Sun Apr 23 2023 Gris Ge <fge@redhat.com> - 2.2.10-2
- Do not pin NIC if `net.ifnames=0`

* Thu Mar 23 2023 Gris Ge <fge@redhat.com> - 2.2.9-1
- Upgrade to 2.2.9

* Sun Mar 12 2023 Gris Ge <fge@redhat.com> - 2.2.8-1
- Upgrade to 2.2.8

* Fri Feb 17 2023 Gris Ge <fge@redhat.com> - 2.2.7-1
- Upgrade to 2.2.7

* Thu Feb 09 2023 Fernando Fernandez Mancera <ferferna@redhat.com> - 2.2.6-1
- Upgrade to 2.2.6

* Thu Jan 26 2023 Fernando Fernandez Mancera <ferferna@redhat.com> - 2.2.5-1
- Upgrade to 2.2.5

* Thu Jan 19 2023 Fernando Fernandez Mancera <ferferna@redhat.com> - 2.2.4-1
- Upgrade to 2.2.4

* Wed Jan 11 2023 Gris Ge <fge@redhat.com> - 2.2.3-3
- Fix OVSDB verification error

* Tue Jan 10 2023 Gris Ge <fge@redhat.com> - 2.2.3-2
- Enable error message for rpm CI gating

* Mon Jan 09 2023 Gris Ge <fge@redhat.com> - 2.2.3-1
- Upgrade to 2.2.3

* Thu Dec 15 2022 Gris Ge <fge@redhat.com> - 2.2.2-2
- Fix regression on VRF interface.

* Wed Dec 14 2022 Gris Ge <fge@redhat.com> - 2.2.2-1
- Upgrade to 2.2.2

* Thu Dec 01 2022 Fernando Fernandez Mancera <ferferna@redhat.com> - 2.2.2-0.alpha.20221201.c8c776e9
- Upgrade to 2.2.2-0.alpha.20221201.c8c776e9

* Wed Nov 16 2022 Fernando Fernandez Mancera <ferferna@redhat.com> - 2.2.1-1
- Upgrade to 2.2.1

* Thu Nov 10 2022 Fernando Fernandez Mancera <ferferna@redhat.com> - 2.2.1-0.alpha.20221110.a9cee09d
- Upgrade to 2.2.1-0.alpha.20221110.a9cee09d

* Mon Oct 17 2022 Gris Ge <fge@redhat.com> - 2.2.0-1
- Upgrade to 2.2.0

* Fri Oct 14 2022 Fernando Fernandez Mancera <ferferna@redhat.com> - 2.2.0-0.alpha.20221014.e54d9ae0
- Upgrade to 2.2.0-alpha.20221014.e54d9ae0

* Mon Aug 15 2022 Gris Ge <fge@rehda.tcom> - 2.1.4-1
- Upgrade to 2.1.4

* Thu Jul 28 2022 Gris Ge <fge@redhat.com> - 2.1.3-1
- Upgraded to 2.1.3

* Wed Jul 20 2022 Fernando Fernandez Mancera <ferferna@redhat.com> - 2.1.3-20220720.cf972e4d
- Upgrade to nmstate-2.1.3-20220720.cf972e4d

* Thu Jul 14 2022 Gris Ge <fge@redhat.com> - 2.1.3-20220714.81d80992
- Upgrade to nmstate-2.1.3-20220714.81d80992

* Thu Jun 30 2022 Fernando Fernandez Mancera <ferferna@redhat.com> - 2.1.2-1
- Upgrade to 2.1.2

* Mon Jun 13 2022 Fernando Fernandez Mancera <ferferna@redhat.com> - 2.1.1-1
- Upgrade to 2.1.1

* Thu Jun 02 2022 Fernando Fernandez Mancera <ferferna@redhat.com> - 2.1.1-0.alpha.20220602.5accbd1
- Upgrade to nmstate-2.1.1-0.alpha.20220602.5accbd1

* Thu May 19 2022 Fernando Fernandez Mancera <ferferna@redhat.com> - 2.1.1-0.alpha.20220519.437e4a9
- Upgrade to nmstate-2.1.1-0.alpha.20220519.437e4a9

* Fri Apr 22 2022 Gris Ge <fge@redhat.com> - 2.1.0-1
- Upgrade to 2.1.0

* Tue Apr 19 2022 Gris Ge <fge@redhat.com> - 2.1.0-0.alpha.20220419.d613311d
- Upgrade to nmstate-2.1.0-0.alpha.20220419.d613311d

* Thu Apr 07 2022 Fernando Fernandez Mancera <ferferna@redhat.com> - 2.1.0-0.alpha.20220407
- Upgrade to nmstate-2.1.0-0.alpha.20220407

* Fri Mar 11 2022 Gris Ge <fge@redhat.com> - 2.1.0-0.alpha.20220311.6f7c2be
- Upgrade to nmstate-2.1.0-0.alpha.20220311.6f7c2be

* Thu Feb 24 2022 Gris Ge <fge@redhat.com> - 2.0.0-2
- Force python3-libnmstate and nmstate-plugin-ovsdb as noarch. RHBZ#1996575

* Wed Feb 16 2022 Fernando Fernandez Mancera <ferferna@redhat.com> - 2.0.0-1
- Upgrade to 2.0.0. RHBZ#1996575

* Thu Jan 13 2022 Gris Ge <fge@redhat.com> - 2.0.0-0.7.alpha6
- Add gating.yaml. RHBZ#1996575

* Wed Jan 12 2022 Gris Ge <fge@redhat.com> - 2.0.0-0.6.alpha6
- Upgrade to 2.0.0. alpha 6. Resolves: RHBZ#1996575

* Thu Dec 16 2021 Fernando Fernandez Mancera <ferferna@redhat.com> - 2.0.0-0.5.alpha5
- Upgrade to 2.0.0 alpha 5. Resolves: RHBZ#1996575
- Fix release number.

* Thu Dec 09 2021 Gris Ge <fge@redhat.com> - 2.0.0-0.1.alpha4
- Upgrade to 2.0.0 alpha 4. Resolves: RHBZ#1996575

* Thu Sep 23 2021 Ana Cabral <acabral@redhat.com> - 2.0.0-0.4.alpha3
- Upgrade to 2.0.0 alpha 3. Resolves: RHBZ#1996575
- Remove connection renaming behaviour. Resolves: RHBZ#1998222
- Add prefixes to OVS bridges and interfaces connections. Resolves: RHBZ#1998218
- Improve OVS bridge start with nmstate. Resolves: RHBZ#1660250

* Mon Aug 09 2021 Mohan Boddu <mboddu@redhat.com> - 2.0.0-0.3.alpha2
- Rebuilt for IMA sigs, glibc 2.34, aarch64 flags
  Related: rhbz#1991688

* Wed Jul 14 2021 Gris Ge <fge@redhat.com> - 2.0.0-0.2.alpha2
- Upgrade to 2.0.0 alpha2

* Fri Jul 02 2021 Wen Liang <wenliang@redhat.com> - 2.0.0-0.1
- Upgrade to 2.0.0 alpha1

* Fri Jun 18 2021 Wen Liang <wenliang@redhat.com> - 1.1.0-0.3
- Fix the 'Release' error. Resolves: RHBZ#1962381

* Thu Jun 10 2021 Wen Liang <wenliang@redhat.com> - 1.1.0-0.3
- Upgrade to 1.1.0 alpha3

* Thu May 27 2021 Wen Liang <wenliang@redhat.com> - 1.1.0-0.1
- Upgrade to 1.1.0 alpha1

* Fri Apr 16 2021 Mohan Boddu <mboddu@redhat.com> - 1.0.2-3
- Rebuilt for RHEL 9 BETA on Apr 15th 2021. Related: rhbz#1947937

* Sun Feb 21 2021 Fernando Fernandez Mancera <ferferna@redhat.com> - 1.0.2-2
- Add missing source to source file

* Sun Feb 21 2021 Fernando Fernandez Mancera <ferferna@redhat.com> - 1.0.2-1
- Upgrade to 1.0.2

* Tue Jan 26 2021 Fedora Release Engineering <releng@fedoraproject.org> - 1.0.1-2
- Rebuilt for https://fedoraproject.org/wiki/Fedora_34_Mass_Rebuild

* Tue Jan 19 2021 Fernando Fernandez Mancera <ferferna@redhat.com> - 1.0.1-1
- Upgrade to 1.0.1

* Tue Dec 08 2020 Fernando Fernandez Mancera <ferferna@redhat.com> - 1.0.0-1
- Upgrade to 1.0.0

* Thu Oct 22 2020 Fernando Fernandez Mancera <ferferna@redhat.com> - 0.4.1-1
- Upgrade to 0.4.1

* Tue Oct 13 2020 Gris Ge <fge@redhat.com> - 0.4.0-2
- Fix the ELN build by put ovs stuff as soft requirement.

* Sun Sep 20 2020 Gris Ge <fge@redhat.com> - 0.4.0-1
- Upgrade to 0.4.0

* Mon Aug 31 2020 Fernando Fernandez Mancera <ferferna@redhat.com> - 0.3.5-1
- Update to 0.3.5

* Tue Jul 28 2020 Fedora Release Engineering <releng@fedoraproject.org> - 0.3.4-2
- Rebuilt for https://fedoraproject.org/wiki/Fedora_33_Mass_Rebuild

* Sat Jul 25 2020 Fernando Fernandez Mancera <ferferna@redhat.com> - 0.3.4-1
- Update to 0.3.4
- Sync. with upstream specfile

* Thu Jul 02 2020 Fernando Fernandez Mancera <ferferna@redhat.com> - 0.3.3-1
- Update to 0.3.3

* Tue Jun 16 2020 Fernando Fernandez Mancera <ferferna@redhat.com> - 0.3.2-1
- Update to 0.3.2
- Sync with upstream specfile

* Tue Jun 09 2020 Fernando Fernandez Mancera <ferferna@redhat.com> - 0.3.1-1
- Update to 0.3.1

* Tue May 26 2020 Miro Hrončok <mhroncok@redhat.com> - 0.3.0-5
- Rebuilt for Python 3.9

* Fri May 08 2020 Fernando Fernandez Mancera <ferferna@redhat.com> - 0.3.0-4
- Fix source path

* Fri May 08 2020 Fernando Fernandez Mancera <ferferna@redhat.com> - 0.3.0-3
- Fix signature verification

* Fri May 08 2020 Fernando Fernandez Mancera <ferferna@redhat.com> - 0.3.0-2
- Update signature verification

* Fri May 08 2020 Fernando Fernandez Mancera <ferferna@redhat.com> - 0.3.0-1
- Update to 0.3.0
- Sync with upstream specfile

* Tue Apr 21 2020 Fernando Fernandez Mancera <ferferna@redhat.com> - 0.2.10-1
- Update to 0.2.10

* Thu Mar 26 2020 Fernando Fernandez Mancera <ferferna@redhat.com> - 0.2.9-1
- Update to 0.2.9

* Fri Mar 13 2020 Fernando Fernandez Mancera <ferferna@redhat.com> - 0.2.8-1
- Update to 0.2.8

* Wed Mar 04 2020 Fernando Fernandez Mancera <ferferna@redhat.com> - 0.2.7-1
- Update to 0.2.7

* Mon Feb 24 2020 Fernando Fernandez Mancera <ferferna@redhat.com> - 0.2.6-1
- Update to 0.2.6

* Wed Feb 19 2020 Fernando Fernandez Mancera <ferferna@redhat.com> - 0.2.5-1
- Update to 0.2.5
- Sync with upstream specfile

* Wed Feb 12 2020 Fernando Fernandez Mancera <ferferna@redhat.com> - 0.2.4-1
- Update to 0.2.4

* Wed Feb 05 2020 Fernando Fernandez Mancera <ferferna@redhat.com> - 0.2.3-1
- Update to 0.2.3

* Tue Feb 04 2020 Fernando Fernandez Mancera <ferferna@redhat.com> - 0.2.2-1
- Update to 0.2.2
- Sync with upstream specfile

* Wed Jan 29 2020 Fedora Release Engineering <releng@fedoraproject.org> - 0.2.1-3
- Rebuilt for https://fedoraproject.org/wiki/Fedora_32_Mass_Rebuild

* Tue Jan 14 2020 Fernando Fernandez Mancera <ferferna@redhat.com> - 0.2.1-2
- Fix changelog

* Tue Jan 14 2020 Fernando Fernandez Mancera <ferferna@redhat.com> - 0.2.1-1
- Update to 0.2.1

* Tue Dec 03 2019 Fernando Fernandez Mancera <ferferna@redhat.com> - 0.2.0-2
- Fix changelog

* Tue Dec 03 2019 Fernando Fernandez Mancera <ferferna@redhat.com> - 0.2.0-1
- Update to 0.2.0

* Mon Dec 02 2019 Till Maas <opensource@till.name> - 0.1.1-1
- Update to 0.1.1
- Sync with upstream specfile

* Thu Oct 03 2019 Miro Hrončok <mhroncok@redhat.com> - 0.0.8-3
- Rebuilt for Python 3.8.0rc1 (#1748018)

* Mon Aug 19 2019 Miro Hrončok <mhroncok@redhat.com> - 0.0.8-2
- Rebuilt for Python 3.8

* Fri Jul 26 2019 Gris Ge <fge@redhat.com> - 0.0.8-1
- Upgrade to 0.0.8.

* Thu Jul 25 2019 Fedora Release Engineering <releng@fedoraproject.org> - 0.0.7-3
- Rebuilt for https://fedoraproject.org/wiki/Fedora_31_Mass_Rebuild

* Fri Jun 14 2019 Gris Ge <fge@redhat.com> - 0.0.7-2
- Workaround broken dbus-python packaging:
   https://bugzilla.redhat.com/show_bug.cgi?id=1654774

* Fri Jun 14 2019 Gris Ge <fge@redhat.com> - 0.0.7-1
- Upgrade to 0.0.7

* Sun May 05 2019 Gris Ge <fge@redhat.com> - 0.0.6-1
- Upgrade to 0.0.6

* Fri Apr 12 2019 Gris Ge <fge@redhat.com - 0.0.5-2
- Add missing runtime requirement: python3-dbus

* Tue Mar 12 2019 Gris Ge <fge@redhat.com> - 0.0.5-1
- Upgrade to 0.0.5

* Fri Feb 01 2019 Fedora Release Engineering <releng@fedoraproject.org> - 0.0.4-3
- Rebuilt for https://fedoraproject.org/wiki/Fedora_30_Mass_Rebuild

* Tue Jan 29 2019 Till Maas <opensource@till.name> - 0.0.4-2
- Sync with upstream spec
- Use Recommends for NetworkManager
- Add Suggests for NetworkManager-ovs
- package examples as doc

* Thu Jan 24 2019 Gris Ge <fge@redhat.com> - 0.0.4-1
- Upgrade to 0.0.4.

* Mon Jan 21 2019 Gris Ge <fge@redhat.com> - 0.0.3-3
- Add missing runtime dependency for nmstatectl.

* Wed Jan 02 2019 Gris Ge <fge@redhat.com> - 0.0.3-2
- Add source file PGP verification.

* Thu Dec 20 2018 Gris Ge <fge@redhat.com> - 0.0.3-1
- Upgrade to 0.0.3.

* Mon Dec 03 2018 Gris Ge <fge@redhat.com> - 0.0.2-2
- Trival RPM SPEC fix.

* Wed Nov 28 2018 Gris Ge <fge@redhat.com> - 0.0.2-1
- Initial release.
