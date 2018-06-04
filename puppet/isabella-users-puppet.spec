%{!?python_sitelib: %global python_sitelib %(%{__python} -c "from distutils.sysconfig import get_python_lib; print(get_python_lib())")}

Name:           isabella-users-puppet
Version:        0.1.0
Release:        2%{?dist}.srce
Summary:        Scripts for updating Puppet yaml with user accounts
Group:          Applications/System
License:        GPL
URL:            https://github.com/vrdel/isabella-users 
Source0:        %{name}-%{version}.tar.gz
BuildRoot:      %{_tmppath}/%{name}-%{version}-%{release}-root-%(%{__id_u} -n)
BuildArch:      noarch 
BuildRequires:  python2-devel
Requires:       python-unidecode
Requires:       python-argparse
Requires:       python-sqlalchemy
Requires:       python-requests
Requires:       PyYAML

%define underscore() %(echo %1 | sed 's/-/_/g')

%description
Scripts for updating Puppet yaml with user accounts

%prep
%setup -q

%build
%{__python} setup.py build

%install
rm -rf $RPM_BUILD_ROOT
%{__python} setup.py install --skip-build --root $RPM_BUILD_ROOT --record=INSTALLED_FILES
install --directory --mode 755 $RPM_BUILD_ROOT/%{_localstatedir}/log/%{name}/
install --directory --mode 755 $RPM_BUILD_ROOT/%{_sharedstatedir}/%{name}/
install --directory --mode 755 $RPM_BUILD_ROOT/%{_sharedstatedir}/%{name}/backup
install --directory %{buildroot}/%{_libexecdir}/%{name}

%clean
rm -rf $RPM_BUILD_ROOT

%files -f INSTALLED_FILES
%dir %{_sysconfdir}/%{name}/
%config %attr(600,root,root) %{_sysconfdir}/%{name}/puppet.conf
%dir %{python_sitelib}/%{underscore %{name}}/
%{python_sitelib}/%{underscore %{name}}/*.py[co]
%dir %{_localstatedir}/log/%{name}/
%dir %{_sharedstatedir}/%{name}/
%dir %{_sharedstatedir}/%{name}/backup
%attr(0755,root,root) %dir %{_libexecdir}/%{name}
%attr(0755,root,root) %{_libexecdir}/%{name}/*.py*

%changelog
* Mon Jun 4 2018 Daniel Vrcic <dvrcic@srce.hr> - 0.1.0-2%{?dist}
- added Logger definition in puppet update-userdb
* Mon Jun 4 2018 Daniel Vrcic <dvrcic@srce.hr> - 0.1.0-1%{?dist}
- first release
