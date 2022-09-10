%{!?_httpd_mmn: %{expand: %%global _httpd_mmn %%(cat %{_includedir}/httpd/.mmn 2>/dev/null || echo 0-0)}}
%{!?_httpd_confdir:     %{expand: %%global _httpd_confdir     %%{_sysconfdir}/httpd/conf.d}}
%{!?_httpd_modconfdir:  %{expand: %%global _httpd_modconfdir  %%{_sysconfdir}/httpd/conf.d}}
%{!?_httpd_moddir:      %{expand: %%global _httpd_moddir      %%{_libdir}/httpd/modules}}
%{!?ruby_vendorlibdir: %global ruby_vendorlibdir %(ruby -rrbconfig -e 'puts RbConfig::CONFIG["vendorlibdir"]')}
%{!?ruby_vendorarchdir: %global ruby_vendorarchdir %(ruby -rrbconfig -e 'puts RbConfig::CONFIG["vendorarchdir"]')}
%global passenger_ruby_libdir %{ruby_vendorlibdir}

Name:passenger
Summary: Phusion Passenger application server
Version: 6.0.8
Release: 4
License: Boost and BSD and MIT and zlib
URL: https://www.phusionpassenger.com

Source: http://s3.amazonaws.com/phusion-passenger/releases/%{name}-%{version}.tar.gz
Source10: passenger.logrotate
Source11: passenger-selinux.te
Source100: apache-passenger.conf.in
Source101: apache-passenger-module.conf
Source102: passenger.tmpfiles

Requires: rubygems rubygem(rack) rubygem(rake) ruby(release)

BuildRequires: gcc, gcc-c++ httpd-devel ruby ruby-devel rubygems rubygems-devel
BuildRequires: rubygem(rake) >= 0.8.1 rubygem(rack) zlib-devel pcre-devel
BuildRequires: openssl-devel libcurl-devel jsoncpp-devel perl

Provides: bundled(boost)  = 1.69.0

Obsoletes: rubygem-passenger < %{version}-%{release}
Provides:  rubygem-passenger = %{version}-%{release}
Provides:  rubygem-passenger%{?_isa} = %{version}-%{release}

Obsoletes: rubygem-passenger-devel < %{version}-%{release}
Obsoletes: rubygem-passenger-native < %{version}-%{release}
Obsoletes: rubygem-passenger-native-libs < %{version}-%{release}

%description
Phusion Passenger® is a web server and application server, designed to be fast,
robust and lightweight. It takes a lot of complexity out of deploying web apps,
adds powerful enterprise-grade features that are useful in production,
and makes administration much easier and less complex. It supports Ruby,
Python, Node.js and Meteor.

%package -n mod_passenger
Summary: Apache Module for Phusion Passenger
BuildRequires: httpd-devel
Requires: httpd-mmn = %{_httpd_mmn}
Requires: %{name}%{?_isa} = %{version}-%{release}

%description -n mod_passenger
This package contains the pluggable Apache server module for Phusion Passenger®.

%package devel
Summary: Phusion Passenger development files
Requires: %{name}%{?_isa} = %{version}-%{release}
Provides: bundled(boost-devel) = %{bundled_boost_version}

%description devel
This package contains development files for Phusion Passenger®. Installing this
package allows it to compile native extensions for non-standard Ruby interpreters,
and allows Passenger Standalone to use a different Nginx core version.

%package help
Summary: Phusion Passenger documentation
Requires: %{name} = %{version}-%{release}
Obsoletes: rubygem-passenger-doc < %{version}-%{release}
Provides:  rubygem-passenger-doc = %{version}-%{release}
Obsoletes: %{name}-doc < %{version}-%{release}
Provides:  %{name}-doc = %{version}-%{release}
BuildArch: noarch

%description help
This package contains documentation files for Phusion Passenger®.

%prep
%autosetup -n %{name}-%{version}

%build
export EXTRA_CFLAGS="${CFLAGS:-%optflags} -Wno-deprecated"
export EXTRA_CXXFLAGS="${CXXFLAGS:-%optflags} -Wno-deprecated"

export EXTRA_CFLAGS=`echo "$EXTRA_CFLAGS" | sed 's|-O2||g'`
export EXTRA_CXXFLAGS=`echo "$EXTRA_CXXFLAGS" | sed 's|-O2||g'`
export OPTIMIZE=yes

export CACHING=false

export CCACHE_COMPRESS=1
export CCACHE_COMPRESSLEVEL=3

export LANG=en_US.UTF-8
export LANGUAGE=en_US.UTF-8
export LC_ALL=en_US.UTF-8

rake -m fakeroot \
    NATIVE_PACKAGING_METHOD=rpm \
    FS_PREFIX=%{_prefix} \
    FS_BINDIR=%{_bindir} \
    FS_SBINDIR=%{_sbindir} \
    FS_DATADIR=%{_datadir} \
    FS_LIBDIR=%{_libdir} \
    FS_DOCDIR=%{_docdir} \
    RUBYLIBDIR=%{ruby_vendorlibdir} \
    RUBYARCHDIR=%{ruby_vendorarchdir} \
    APACHE2_MODULE_PATH=%{_httpd_moddir}/mod_passenger.so


%install
export LANG=en_US.UTF-8
export LANGUAGE=en_US.UTF-8
export LC_ALL=en_US.UTF-8

%{__rm} -rf %{buildroot}
%{__mkdir} %{buildroot}
%{__cp} -a pkg/fakeroot/* %{buildroot}/

%{__mkdir_p} %{buildroot}%{_httpd_confdir} %{buildroot}%{_httpd_modconfdir}
%{__sed} -e 's|@PASSENGERROOT@|%{_datadir}/passenger/phusion_passenger/locations.ini|g' %{SOURCE100} > passenger.conf
%{__sed} -i -e '/^# *Require all granted/d' passenger.conf

./dev/install_scripts_bootstrap_code.rb --ruby %{passenger_ruby_libdir} \
    %{buildroot}%{_bindir}/* \
    %{buildroot}%{_sbindir}/* \
    `find %{buildroot} -name rack_handler.rb`

%if "%{_httpd_modconfdir}" == "%{_httpd_confdir}"
    %{__cat} %{SOURCE101} passenger.conf > passenger-combined.conf
    touch -r %{SOURCE100} passenger-combined.conf
    %{__install} -pm 0644 passenger-combined.conf %{buildroot}%{_httpd_confdir}/passenger.conf
%else
    touch -r %{SOURCE100} passenger.conf
    %{__install} -pm 0644 passenger.conf %{buildroot}%{_httpd_confdir}/passenger.conf
    %{__install} -pm 0644 %{SOURCE101} %{buildroot}%{_httpd_modconfdir}/10-passenger.conf
    touch -r %{SOURCE101} %{buildroot}%{_httpd_modconfdir}/10-passenger.conf
%endif

%{__mkdir_p} %{buildroot}%{_localstatedir}/log/passenger-analytics
%{__mkdir_p} %{buildroot}%{_localstatedir}/run/passenger-instreg
%{__mkdir_p} %{buildroot}%{_usr}/lib/tmpfiles.d
%{__install} -m 644 -p %{SOURCE102} \
	%{buildroot}%{_usr}/lib/tmpfiles.d/passenger.conf

%{__mkdir_p} %{buildroot}%{_sysconfdir}/logrotate.d
%{__install} -pm 0644 %{SOURCE10} %{buildroot}%{_sysconfdir}/logrotate.d/passenger

%{__mkdir_p} %{buildroot}%{_mandir}/man1
%{__mkdir_p} %{buildroot}%{_mandir}/man8
%{__cp} man/*.1 %{buildroot}%{_mandir}/man1
%{__cp} man/*.8 %{buildroot}%{_mandir}/man8

%{__chmod} +x %{buildroot}%{_datadir}/passenger/helper-scripts/wsgi-loader.py

find %{buildroot}%{_bindir}  %{buildroot}%{_datadir}/passenger/helper-scripts/ -type f | xargs sed -i 's|^#!/usr/bin/env ruby$|#!/usr/bin/ruby|'
sed -i 's|^#!/usr/bin/env python$|#!/usr/bin/python3|' %{buildroot}%{_datadir}/passenger/helper-scripts/wsgi-loader.py

%files
%doc LICENSE CONTRIBUTORS CHANGELOG
%{_bindir}/*
%exclude %{_bindir}/%{name}-install-*-module
%{_sbindir}/*
%{_usr}/lib/tmpfiles.d/passenger.conf
%{_datadir}/passenger/helper-scripts
%{_datadir}/passenger/templates
%{_datadir}/passenger/standalone_default_root
%{_datadir}/passenger/node
%{_datadir}/passenger/*.types
%{_datadir}/passenger/*.crt
%{_datadir}/passenger/*.txt
%{_datadir}/passenger/*.pem
%{_datadir}/passenger/*.p12
%dir %{_localstatedir}/log/passenger-analytics
%dir %attr(755, root, root) %{_localstatedir}/run/passenger-instreg
%{_sysconfdir}/logrotate.d/passenger
%{passenger_ruby_libdir}/*
%{_libdir}/passenger/support-binaries
%{ruby_vendorarchdir}/passenger_native_support.so

%files devel
%{_datadir}/passenger/ngx_http_passenger_module
%{_datadir}/passenger/ruby_extension_source
%{_datadir}/passenger/include
%{_libdir}/%{name}/common
%exclude %{_libdir}/%{name}/nginx_dynamic

%files -n mod_passenger
%config(noreplace) %{_httpd_modconfdir}/*.conf
%if "%{_httpd_modconfdir}" != "%{_httpd_confdir}"
    %config(noreplace) %{_httpd_confdir}/*.conf
%endif
%{_httpd_moddir}/mod_passenger.so

%files help
%{_docdir}/%{name}/*
%{_mandir}/*/*

%changelog
* Sat Sep 10 2022 yangchenguang <yangchenguang@uniontech.com> - 6.0.8-4
- fix passenger load error

* Mon Apr 25 2022 caodongxia<caodongxia@h-partners.com> - 6.0.8-3
- add buildRequires to resolve compilation failure

* Tue Oct 19 2021 zhangweiguo <zhangweiguo2@huawei.com> - 6.0.8-2
- add rake option -m

* Tue Aug 10 2021 yixiangzhike <zhangxingliang3@huawei.com> - 6.0.8-1
- update version to 6.0.8

* Sat Jan 23 2021 zoulin <zoulin13@huawei.com> - 6.0.7-1
- update version to 6.0.7

* Wed Mar 4 2020 openEuler Buildteam <buildteam@openeuler.org> - 6.0.4-2
- Package Init
