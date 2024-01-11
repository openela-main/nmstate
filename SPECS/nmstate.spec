%?python_enable_dependency_generator
%define srcname nmstate
%define libname libnmstate

Name:           nmstate
Version:        1.4.4
Release:        3%{?dist}
Summary:        Declarative network manager API
License:        LGPLv2+
URL:            https://github.com/%{srcname}/%{srcname}
Source0:        %{url}/releases/download/v%{version}/%{srcname}-%{version}.tar.gz
Source1:        %{url}/releases/download/v%{version}/%{srcname}-%{version}.tar.gz.asc
Source2:        https://www.nmstate.io/nmstate.gpg
Source3:        %{url}/releases/download/v%{version}/%{srcname}-vendor-%{version}.tar.xz
# Patches 0X are reserved to downstream only
Patch0:         BZ_2132570-nm-reverse-IPv6-order-before-adding-them-to-setting.patch
Patch1:         BZ_2203277-ip-Support-static-route-with-auto-ip.patch
BuildRequires:  python3-devel
BuildRequires:  python3-setuptools
BuildRequires:  gnupg2
BuildRequires:  rust-toolset
BuildRequires:  pkg-config
Requires:       python3-setuptools
Requires:       python3-%{libname} = %{?epoch:%{epoch}:}%{version}-%{release}

%description
Nmstate is a library with an accompanying command line tool that manages host
networking settings in a declarative manner and aimed to satisfy enterprise
needs to manage host networking through a northbound declarative API and multi
provider support on the southbound.


%package -n python3-%{libname}
Summary:        nmstate Python 3 API library
BuildArch:      noarch
Requires:       NetworkManager-libnm >= 1:1.26.0
# Use Recommends for NetworkManager because only access to NM DBus is required,
# but NM could be running on a different host
Recommends:     NetworkManager
# Avoid automatically generated profiles
Recommends:     NetworkManager-config-server
# Use Suggests for NetworkManager-ovs and NetworkManager-team since it is only
# required for OVS and team support
Suggests:       NetworkManager-ovs
Suggests:       NetworkManager-team
Requires:       nispor
Requires:       python3dist(varlink)

%package -n nmstate-plugin-ovsdb
Summary:        nmstate plugin for OVS database manipulation
BuildArch:      noarch
Requires:       python3-%{libname} = %{?epoch:%{epoch}:}%{version}-%{release}
# The python-openvswitch rpm pacakge is not in the same repo with nmstate,
# hence state it as Recommends, no requires.
Recommends:     python3dist(ovs)


%package libs
Summary:        C binding of nmstate
License:        ASL 2.0

%package devel
Summary:        C binding development files of nmstate
License:        ASL 2.0
Requires:       nmstate-libs%{?_isa} = %{?epoch:%{epoch}:}%{version}-%{release}

%description libs
This package contains the C binding of nmstate.

%description devel
This package contains the C binding development files of nmstate.

%description -n python3-%{libname}
This package contains the Python 3 library for nmstate.

%description -n nmstate-plugin-ovsdb
This package contains the nmstate plugin for OVS database manipulation.

%prep
gpg2 --import --import-options import-export,import-minimal %{SOURCE2} > ./gpgkey-mantainers.gpg
gpgv2 --keyring ./gpgkey-mantainers.gpg %{SOURCE1} %{SOURCE0}
%autosetup -p1

pushd rust
# Source3 is vendored dependencies
%cargo_prep -V 3

# The cargo_prep will create `.cargo/config` which take precedence over
# `.cargo/config.toml` shipped by upstream which fix the SONAME of cdylib.
# To workaround that, merge upstream rustflags into cargo_prep created one.
_FLAGS=`sed -ne 's/rustflags = "\(.\+\)"/\1/p' .cargo/config.toml`
sed -i -e "s/rustflags = \[\(.\+\), \]$/rustflags = [\1, \"$_FLAGS\"]/" \
    .cargo/config
rm .cargo/config.toml

popd

%build
%py3_build

pushd rust
make
popd

%install
%py3_install
pushd rust
env SKIP_PYTHON_INSTALL=1 \
   PREFIX=%{_prefix} \
   LIBDIR=%{_libdir} \
   %make_install
popd

%files
%doc README.md
%doc examples/
%{_mandir}/man8/nmstatectl.8*
%{_mandir}/man8/nmstate-autoconf.8*
%{python3_sitelib}/nmstatectl
%{_bindir}/nmstatectl
%{_bindir}/nmstatectl-rust
%{_bindir}/nmstate-autoconf

%files -n python3-%{libname}
%license LICENSE
%{python3_sitelib}/%{libname}
%{python3_sitelib}/%{srcname}-*.egg-info/
%exclude %{python3_sitelib}/%{libname}/plugins/nmstate_plugin_*
%exclude %{python3_sitelib}/%{libname}/plugins/__pycache__/nmstate_plugin_*

%files -n nmstate-plugin-ovsdb
%{python3_sitelib}/%{libname}/plugins/nmstate_plugin_ovsdb*
%{python3_sitelib}/%{libname}/plugins/__pycache__/nmstate_plugin_ovsdb*

%files libs
%license rust/LICENSE
%{_libdir}/libnmstate.so.*

%files devel
%license LICENSE
%{_libdir}/libnmstate.so
%{_includedir}/nmstate.h
%{_libdir}/pkgconfig/nmstate.pc

%post libs
/sbin/ldconfig

%postun libs
/sbin/ldconfig

%changelog
* Tue May 30 2023 Fernando Fernandez Mancera <ferferna@redhat.com> - 1.4.4-3
- Support static route with auto-ip. RHBZ#2203277

* Mon Apr 24 2023 Gris Ge <fge@redhat.com> - 1.4.4-2
- Enable CI gating.

* Sun Apr 23 2023 Gris Ge <fge@redhat.com> - 1.4.4-1
- Upgrade to nmstate 1.4.4

* Wed Mar 29 2023 Gris Ge <fge@redhat.com> - 1.4.3-1
- Upgrade to nmstate 1.4.3. RHBZ#2179899

* Mon Feb 27 2023 Gris Ge <fge@redhat.com> - 1.4.2-4
- Ignore undesired iface config. RHBZ#2160416

* Thu Feb 23 2023 Gris Ge <fge@redhat.com> - 1.4.2-3
- Additional patch for SR-IOV. RHBZ#2160416

* Wed Feb 22 2023 Gris Ge <fge@redhat.com> - 1.4.2-2
- Enable YAML API in rust clib.

* Sat Feb 18 2023 Gris Ge <fge@redhat.com> - 1.4.2-1
- Upgrade to nmstate 1.4.2

* Mon Jan 09 2023 Gris Ge <fge@redhat.com> - 1.4.1-1
- Upgrade to nmstate-1.4.1

* Wed Dec 14 2022 Gris Ge <fge@redhat.com> - 1.4.0-1
- Upgrade to nmstate-1.4.0

* Thu Dec 01 2022 Fernando Fernandez Mancera <ferferna@redhat.com> - 1.4.0.alpha.20221201
- Upgrade to nmstate-1.4.0.alpha.20221201

* Fri Nov 18 2022 Fernando Fernandez Mancera <ferferna@redhat.com> - 1.3.4.alpha.20221118
- Upgrade to nmstate-1.3.4.alpha.20221118

* Mon Oct 24 2022 Fernando Fernandez Mancera <ferferna@redhat.com> - 1.3.4.alpha.20221024
- Undo the branching misdone by Fernando.

* Mon Aug 15 2022 Gris Ge <fge@redhat.com> - 1.3.3-1
- Upgrade to nmstate-1.3.3

* Tue Aug 02 2022 Fernando Fernandez Mancera <ferferna@redhat.com> - 1.3.2-1
- Upgrade to nmstate-1.3.2

* Wed Jul 20 2022 Fernando Fernandez Mancera <ferferna@redhat.com> - 1.3.1-1
- Upgrade to nmstate-1.3.1

* Fri Jul 01 2022 Fernando Fernandez Mancera <ferferna@redhat.com> - 1.3.1-0.alpha.20220701
- Upgrade to nmstate-1.3.1-0.alpha.20220701

* Mon Jun 13 2022 Fernando Fernandez Mancera <ferferna@redhat.com> - 1.3.0-1
- Upgrade to nmstate-1.3.0-1

* Thu May 05 2022 Fernando Fernandez Mancera <ferferna@redhat.com> - 1.3.0-0.alpha.20220505
- Upgrade to nmstate-1.3.0.alpha.20220505

* Thu Apr 07 2022 Fernando Fernandez Mancera <ferferna@redhat.com> - 1.3.0-0.alpha.20220407
- Upgrade to nmstate-1.3.0.alpha.20220407

* Thu Mar 10 2022 Gris Ge <fge@redhat.com> - 1.3.0-0.alpha.20220310
Upgrade to nmstate-1.3.0-0.alpha.20220310

* Mon Feb 14 2022 Gris Ge <fge@redhat.com> - 1.2.1-1
- Upgrade to 1.2.1. RHBZ#1996618

* Thu Jan 27 2022 Gris Ge <ferferna@redhat.com> - 1.2.1-0.2.alpha2
- Upgrade to 1.2.1 alpha2. RHBZ#1996618

* Thu Jan 13 2022 Gris Ge <fge@redhat.com> - 1.2.1-0.1.alpha1
- Upgrade to 1.2.1 alpha1. RHBZ#1996618

* Thu Dec 16 2021 Fernando Fernandez Mancera <ferferna@redhat.com> - 1.2.0-1
- Upgrade to 1.2.0. RHBZ#1996618

* Thu Dec 09 2021 Gris Ge <fge@redhat.com> - 1.2.0-0.1.alpha2
- Upgrade to 1.2.0 alpha2. RHBZ#1996618

* Tue Oct 12 2021 Gris Ge <fge@redhat.com> - 1.2.0-0.1.alpha1
- Upgrade to 1.2.0 alpha1.

* Wed Sep 15 2021 Ana Cabral <acabral@redhat.com> - 1.1.1-0.1.alpha1
- Upgrade to 1.1.1 alpha1.
- Canonicalize ipv6 addresses for dns nameservers. RHBZ#1911241
- Throw better error when peer is missing for veth interfaces. RHBZ#1973973

* Tue Jul 27 2021 Gris Ge <fge@redhat.com> - 1.1.0-3
- Fix state=ignore for OVS interface. RHBZ#1944054
- Fix verification for next hop address 0.0.0.0. RHBZ#1985879

* Fri Jul 23 2021 Gris Ge <fge@redhat.com> - 1.1.0-2
- Preserving existing ethtool settings. RHBZ#1984764

* Thu Jul 15 2021 Gris Ge <fge@redhat.com> - 1.1.0-1
- Upgrade to 1.1.0.

* Fri Jul 09 2021 Gris Ge <fge@redhat.com> - 1.1.0-0.7.alpha7
- Upgarde to 1.1.0 alpha7.

* Thu Jul 01 2021 Gris Ge <fge@redhat.com> - 1.1.0-0.6.alpha6
- Upgrade to 1.1.0 alpha6.

* Mon Jun 21 2021 Fernando Fernandez Mancera <ferferna@redhat.com> - 1.1.0-0.5.alpha4
- Upgrade to 1.1.0 alpha4.

* Wed Jun 16 2021 Fernando Fernandez Mancera <ferferna@redhat.com> - 1.1.0-0.4.alpha3
- Rebuild to introduce CI gating tier1 tests. RHBZ#1813357

* Tue Jun 08 2021 Gris Ge <fge@redhat.com> - 1.1.0-0.3.alpha3
- Upgrade to 1.1.0 alpha3.

* Mon Jun 07 2021 Fernando Fernandez Mancera <ferferna@redhat.com> - 1.1.0-0.2
- Upgrade to 1.1.0 alpha2.

* Wed May 19 2021 Wen Liang <wenliang@redhat.com> - 1.1.0-0.1
- Upgrade to 1.1.0 alpha1.

* Tue Apr 20 2021 Fernando Fernandez Mancera <ferferna@redhat.com> - 1.0.3-1
- Upgrade to 1.0.3. RHBZ#1942458

* Fri Mar 26 2021 Fernando Fernandez Mancera <ferferna@redhat.com> - 1.0.2-6
- Rebuild for RHEL 8.5. RHBZ#1935710

* Fri Mar 26 2021 Fernando Fernandez Mancera <ferferna@redhat.com> - 1.0.2-5
- New patch for fixing unmanaged interfaces being managed. RHBZ#1935710

* Tue Feb 23 2021 Gris Ge <fge@redhat.com> - 1.0.2-4
- New patch for SRIOV decrease VF amount. RHBZ#1931355

* Tue Feb 23 2021 Gris Ge <fge@redhat.com> - 1.0.2-3
- Fix actiation failure when decrease VF mount on i40e. RHBZ#1931355

* Tue Feb 23 2021 Gris Ge <fge@redhat.com> - 1.0.2-2
- Fix nmstatectl return code of `set` command. RHBZ#1931751

* Fri Feb 19 2021 Gris Ge <fge@redhat.com> - 1.0.2-1
- Upgrade to 1.0.2.

* Wed Feb 10 2021 Fernando Fernandez Mancera <ferferna@redhat.com> - 1.0.2-0.3
- Fix sources name

* Wed Feb 10 2021 Fernando Fernandez Mancera <ferferna@redhat.com> - 1.0.2-0.2
- Upgrade to 1.0.2 alpha 2

* Tue Jan 26 2021 Fernando Fernandez Mancera <ferferna@redhat.com> - 1.0.2-0.1
- Upgrade to 1.0.2 alpha 1

* Tue Jan 19 2021 Fernando Fernandez Mancera <ferferna@redhat.com> - 1.0.1-1
- Upgrade to 1.0.1. RHBZ#1881287

* Tue Jan 05 2021 Gris Ge <fge@redhat.com> - 1.0.1-0.1
- Upgrade to 1.0.1 alpha 1

* Tue Dec 08 2020 Fernando Fernandez Mancera <ferferna@redhat.com> - 1.0.0-1
- Upgrade to 1.0.0

* Mon Nov 16 2020 Gris Ge <fge@redhat.com> - 1.0.0-0.1
- Upgrade to 1.0.0 alpha 1

* Wed Oct 28 2020 Fernando Fernandez Mancera <ferferna@redhat.com> - 0.4.1-2
- Allow VRF port to hold IP information

* Thu Oct 22 2020 Fernando Fernandez Mancera <ferferna@redhat.com> - 0.4.1-1
- Upgrade to 0.4.1

* Tue Oct 20 2020 Fernando Fernandez Mancera <ferferna@redhat.com> - 0.4.0-3
- Add nispor as a dependency for CI gating

* Tue Oct 20 2020 Fernando Fernandez Mancera <ferferna@redhat.com> - 0.4.0-2
- Rebuild for CI gating
- Remove old patches from the repository

* Mon Sep 14 2020 Fernando Fernandez Mancera <ferferna@redhat.com> - 0.4.0-1
- Upgrade to 0.4.0
- Sync. up with upstream spec file.

* Tue Aug 18 2020 Gris Ge <fge@redhat.com> - 0.3.4-12
- New patch: OVSDB: Allowing remove all OVS ports. RHBZ#1869345

* Tue Aug 18 2020 Gris Ge <fge@redhat.com> - 0.3.4-11
- OVSDB: Allowing remove all OVS ports. RHBZ#1869345

* Thu Aug 06 2020 Gris Ge <fge@redhat.com> - 0.3.4-10
- OVSDB: Preserv old external_ids. RHBZ#1866269

* Tue Aug 04 2020 Gris Ge <fge@redhat.com> - 0.3.4-9
- Fix converting memory only profile to persistent. RHBZ#1859844

* Mon Aug 03 2020 Gris Ge <fge@redhat.com> - 0.3.4-8
- Fix failure when adding ovs bond to existing bridge. RHBZ#1858758

* Thu Jul 30 2020 Gris Ge <fge@redhat.com> - 0.3.4-7
- Remove existing inactivate NM profiles. RHBZ#1862025

* Wed Jul 29 2020 Gris Ge <fge@redhat.com> - 0.3.4-6
- New build to retrigger the CI gating.

* Wed Jul 29 2020 Gris Ge <fge@redhat.com> - 0.3.4-5
- Use new patch. RHBZ#1861668

* Wed Jul 29 2020 Gris Ge <fge@redhat.com> - 0.3.4-4
- Ignore unknown interface. RHBZ#1861668

* Tue Jul 28 2020 Gris Ge <fge@redhat.com> - 0.3.4-3
- Add support NetworkManaged exteranl managed interface. RHBZ#1861263

* Tue Jul 28 2020 Gris Ge <fge@redhat.com> - 0.3.4-2
- Hide MTU for OVS patch port. RHBZ#1858762

* Sat Jul 25 2020 Fernando Fernandez Mancera <ferferna@redhat.com> - 0.3.4-1
- Upgrade to 0.3.4

* Fri Jul 24 2020 Gris Ge <fge@redhat.com> - 0.3.3-3
- Allowing child been marked absent. RHBZ#1859148

* Mon Jul 06 2020 Fernando Fernandez Mancera <ferferna@redhat.com> - 0.3.3-2
- Fix bug 1850698

* Thu Jul 02 2020 Fernando Fernandez Mancera <ferferna@redhat.com> - 0.3.3-1
- Upgrade to 0.3.3

* Mon Jun 29 2020 Gris Ge <fge@redhat.com> - 0.3.2-6
- Improve performance by remove unneeded calls. RHBZ#1820009

* Mon Jun 29 2020 Gris Ge <fge@redhat.com> - 0.3.2-5
- Sort the pretty state with priority. RHBZ#1806474

* Mon Jun 29 2020 Gris Ge <fge@redhat.com> - 0.3.2-4
- Canonicalize IP address. RHBZ#1816612

* Mon Jun 29 2020 Gris Ge <fge@redhat.com> - 0.3.2-3
- Improve VLAN MTU error message. RHBZ#1788763

* Mon Jun 29 2020 Gris Ge <fge@redhat.com> - 0.3.2-2
- Fix bug 1850698

* Mon Jun 15 2020 Fernando Fernandez Mancera <ferferna@redhat.com> - 0.3.2-1
- Upgrade to 0.3.2
- Sync. up with upstream spec file

* Thu Jun 11 2020 Gris Ge <fge@redhat.com> - 0.3.1-1
- Upgrade to 0.3.1

* Wed May 13 2020 Fernando Fernandez Mancera <ferferna@redhat.com> - 0.3.0-1
- Upgrade to 0.3.0
- Sync. up with upstream spec file.
- Update signature verification.

* Tue Mar 31 2020 Fernando Fernandez Mancera <ferferna@redhat.com> - 0.2.9-1
- Upgrade to 0.2.9

* Wed Mar 25 2020 Gris Ge <fge@redhat.com> - 0.2.6-6
- Support 3+ DNS name server(IPv4 only or IPv6 only). RHBZ #1816043

* Fri Mar 20 2020 Gris Ge <fge@redhat.com> - 0.2.6-5
- Support static DNS with DHCP. RHBZ #1815112

* Thu Mar 12 2020 Fernando Fernandez Mancera <ferferna@redhat.com> - 0.2.6-4.8
- Fix bond mac and options regression. RHBZ #1809330

* Mon Mar 09 2020 Gris Ge <fge@redhat.com> - 0.2.6-3.8
- Fix change bond mode. RHBZ #1809330

* Mon Mar 02 2020 Fernando Fernandez Mancera <ferferna@redhat.com> - 0.2.6-2.7
- Fix cmd stuck when trying to create ovs-bond. RHBZ #1806249.

* Tue Feb 25 2020 Gris Ge <fge@redhat.com> - 0.2.6-1
- Upgrade to 0.2.6

* Thu Feb 20 2020 Gris Ge <fge@redhat.com> - 0.2.5-1
- Upgrade to 0.2.5

* Thu Feb 13 2020 Gris Ge <fge@redhat.com> - 0.2.4-2
- Fix failure when editing existing OVS interface. RHBZ #1786935

* Thu Feb 13 2020 Gris Ge <fge@redhat.com> - 0.2.4-1
- Upgrade to 0.2.4

* Wed Feb 05 2020 Fernando Fernandez Mancera <ferferna@redhat.com> - 0.2.3-1
- Upgrade to 0.2.3

* Tue Feb 04 2020 Fernando Fernandez Mancera <ferferna@redhat.com> - 0.2.2-3
- Fix the incorrect source

* Tue Feb 04 2020 Fernando Fernandez Mancera <ferferna@redhat.com> - 0.2.2-2
- Upgrade to 0.2.2

* Wed Jan 22 2020 Gris Ge <fge@redhat.com> - 0.2.0-3.1
- Fix the memeory leak of NM.Client. RHBZ #1784707

* Mon Dec 02 2019 Gris Ge <fge@redhat.com> - 0.2.0-2
- Fix the incorrect source tarbal.

* Mon Dec 02 2019 Gris Ge <fge@redhat.com> - 0.2.0-1
- Upgrade to nmstate 0.2.0

* Mon Dec 02 2019 Gris Ge <fge@redhat.com> - 0.1.1-4
- Fix the problem found by CI gating.

* Mon Dec 02 2019 Gris Ge <fge@redhat.com> - 0.1.1-3
- Bump dist number as RHEL 8.1.1 took 0.1.1-2.

* Mon Dec 02 2019 Gris Ge <fge@redhat.com> - 0.1.1-2
- Upgrade to nmstate 0.1.1.

* Tue Sep 10 2019 Gris Ge <fge@redhat.com> - 0.0.8-15
- Detach slaves without deleting them: RHBZ #1749632

* Fri Sep 06 2019 Gris Ge <fge@redhat.com> - 0.0.8-14
- Preserve (dynamic) IPv6 address base on MAC address: RHBZ #1748825

* Fri Sep 06 2019 Gris Ge <fge@redhat.com> - 0.0.8-13
- Prioritize master interfaces activaction: RHBZ #1749314

* Mon Sep 02 2019 Gris Ge <fge@redhat.com> - 0.0.8-12
- Fix slave activatoin race: RHBZ #1741440

* Mon Sep 02 2019 Gris Ge <fge@redhat.com - 0.0.8-11
- Add NetworkManager-config-server dependency: Fix RHBZ #1740085

* Thu Aug 15 2019 Gris Ge <fge@redhat.com> - 0.0.8-10
- Fix RHBZ #1740125

* Wed Aug 14 2019 Gris Ge <fge@redhat.com> - 0.0.8-9
- Fix RHBZ #1741049

* Wed Aug 14 2019 Gris Ge <fge@redhat.com> - 0.0.8-8
- Fix RHBZ #1740584

* Tue Aug 13 2019 Gris Ge <fge@redhat.com> - 0.0.8-7
- Fix RHBZ #1740554

* Tue Aug 13 2019 Gris Ge <fge@redhat.com> - 0.0.8-6
- Bump release tag as CNV took the -5.

* Tue Aug 13 2019 Gris Ge <fge@redhat.com> - 0.0.8-5
- Bump release tag as CNV took the -4.

* Tue Aug 13 2019 Gris Ge <fge@redhat.com> - 0.0.8-4
- Disable reapply on ipv6 to fix bug 1738101.

* Fri Jul 26 2019 Gris Ge <fge@redhat.com> - 0.0.8-3
- Fix the license to meet Fedora/RHEL guideline.

* Fri Jul 26 2019 Gris Ge <fge@redhat.com> - 0.0.8-2
- Relicense to LGPL2.1+.

* Fri Jul 26 2019 Gris Ge <fge@redhat.com> - 0.0.8-1
- Upgrade to 0.0.8.

* Fri Jun 14 2019 Gris Ge <fge@redhat.com> - 0.0.7-1
- Upgrade to 0.0.7.

* Mon Apr 22 2019 Gris Ge <fge@redhat.com> - 0.0.5-3
- Add missing runtime dependency.

* Thu Mar 21 2019 Gris Ge <fge@redhat.com> - 0.0.5-2
- Rebuild to enable CI testing.

* Mon Mar 18 2019 Gris Ge <fge@redhat.com> - 0.0.5-1
- Initial release
