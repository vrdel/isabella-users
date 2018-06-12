%{!?python_sitelib: %global python_sitelib %(%{__python} -c "from distutils.sysconfig import get_python_lib; print(get_python_lib())")}

Name:           isabella-users-frontend
Version:        0.1.0
Release:        3%{?dist}.srce
Summary:        Scripts for opening user accounts on SRCE Isabella cluster
Group:          Applications/System
License:        GPL
URL:            https://github.com/vrdel/isabella-users 
Source0:        %{name}-%{version}.tar.gz
BuildRoot:      %{_tmppath}/%{name}-%{version}-%{release}-root-%(%{__id_u} -n)
BuildArch:      noarch 
BuildRequires:  python2-devel
Requires:       python-unidecode
Requires:       libuser-python
Requires:       python-argparse
Requires:       python-sqlalchemy0.8
Requires:       python-requests

%define underscore() %(echo %1 | sed 's/-/_/g')

%description
Scripts for opening user accounts on SRCE Isabella cluster

%prep
%setup -q

%build
%{__python} setup.py build

%install
rm -rf $RPM_BUILD_ROOT
%{__python} setup.py install --skip-build --root $RPM_BUILD_ROOT --record=INSTALLED_FILES
install --directory --mode 755 $RPM_BUILD_ROOT/%{_localstatedir}/log/%{name}/
install --directory --mode 755 $RPM_BUILD_ROOT/%{_sharedstatedir}/%{name}/
install --directory %{buildroot}/%{_libexecdir}/%{name}

%clean
rm -rf $RPM_BUILD_ROOT

%files -f INSTALLED_FILES
%dir %{_sysconfdir}/%{name}/
%config(noreplace) %attr(600,root,root) %{_sysconfdir}/%{name}/frontend.conf
%dir %{python_sitelib}/%{underscore %{name}}/
%{python_sitelib}/%{underscore %{name}}/*.py[co]
%dir %{_localstatedir}/log/%{name}/
%dir %{_sharedstatedir}/%{name}/
%attr(0755,root,root) %dir %{_libexecdir}/%{name}
%attr(0755,root,root) %{_libexecdir}/%{name}/*.py*

%changelog
* Tue Jun 12 2018 Daniel Vrcic <dvrcic@srce.hr> - 0.1.0-3%{?dist}
- added log msgs about done actions 
* Mon Jun 4 2018 Daniel Vrcic <dvrcic@srce.hr> - 0.1.0-2%{?dist}
- Cc mail with opened user accounts
* Sun Jun 3 2018 Daniel Vrcic <dvrcic@srce.hr> - 0.1.0-1%{?dist}
- first release
