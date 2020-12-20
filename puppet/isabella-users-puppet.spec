%{!?python_sitelib: %global python_sitelib %(%{__python} -c "from distutils.sysconfig import get_python_lib; print(get_python_lib())")}

%define underscore() %(echo %1 | sed 's/-/_/g')
%define stripc() %(echo %1 | sed 's/el7.centos/el7/')

%if 0%{?el7:1}
%define mydist %{stripc %{dist}}
%else
%define mydist %{dist}
%endif

Name:           isabella-users-puppet
Version:        0.1.7
Release:        1%{?mydist}.srce
Summary:        Scripts for updating Puppet yaml with user accounts
Group:          Applications/System
License:        GPL
URL:            https://github.com/vrdel/isabella-users
Source0:        %{name}-%{version}.tar.gz
BuildRoot:      %{_tmppath}/%{name}-%{version}-%{release}-root-%(%{__id_u} -n)
BuildArch:      noarch
BuildRequires:  python3-devel
Requires:       python3-text-unidecode
Requires:       python3-sqlalchemy
Requires:       python3-requests
Requires:       python3-pyyaml


%description
Scripts for updating Puppet yaml with user accounts

%prep
%setup -q

%build
%{py3_build}

%install
rm -rf $RPM_BUILD_ROOT
%{py3_install "--record=INSTALLED_FILES"}
install --directory --mode 755 $RPM_BUILD_ROOT/%{_localstatedir}/log/%{name}/
install --directory --mode 755 $RPM_BUILD_ROOT/%{_sharedstatedir}/%{name}/
install --directory --mode 755 $RPM_BUILD_ROOT/%{_sharedstatedir}/%{name}/backup
install --directory %{buildroot}/%{_libexecdir}/%{name}

%clean
rm -rf $RPM_BUILD_ROOT

%files -f INSTALLED_FILES
%dir %{_sysconfdir}/%{name}/
%config(noreplace) %attr(600,root,root) %{_sysconfdir}/%{name}/puppet.conf
%config(noreplace) %attr(600,root,root) %{_sysconfdir}/%{name}/users.json
%dir %{python3_sitelib}/%{underscore %{name}}/
%{python3_sitelib}/%{underscore %{name}}/*.py
%dir %{_localstatedir}/log/%{name}/
%dir %{_sharedstatedir}/%{name}/

%attr(0755,root,root) %{_libexecdir}/%{name}/*.py*

%changelog
* Sun Dec 20 2020 Daniel Vrcic <dvrcic@srce.hr> - 0.1.7-1%{?dist}
- bump to Centos 8 and Python 3
* Fri May 22 2020 Daniel Vrcic <dvrcic@srce.hr> - 0.1.6-1%{?dist}
- remove handling of CRO-NGI users
* Thu May 7 2020 Daniel Vrcic <dvrcic@srce.hr> - 0.1.5-1%{?dist}
- skip multiple HTC-only services
* Tue Feb 11 2020 Daniel Vrcic <dvrcic@srce.hr> - 0.1.4-1%{?dist}
- take into account skipusers for projects changes only
* Mon Oct 28 2019 Daniel Vrcic <dvrcic@srce.hr> - 0.1.3-3%{?dist}
- skip HTC only projects
* Tue Sep 17 2019 Daniel Vrcic <dvrcic@srce.hr> - 0.1.3-2%{?dist}
- remove debugger leftover
* Mon Sep 16 2019 Daniel Vrcic <dvrcic@srce.hr> - 0.1.3-1%{?dist}
- handle users with same name and surname
* Wed Jul 3 2019 Daniel Vrcic <dvrcic@srce.hr> - 0.1.2-1%{?dist}
- update associations of existing users to existing projects
* Thu Aug 16 2018 Daniel Vrcic <dvrcic@srce.hr> - 0.1.1-1%{?dist}
- update project's timelines to the most recent
- lookup firstly by AAI uid
- store also AAI uid
- transliterate map user data to ASCII
* Thu Jun 7 2018 Daniel Vrcic <dvrcic@srce.hr> - 0.1.0-3%{?dist}
- do not replace configs on update
- backup yaml with h:m:s timestamp
* Mon Jun 4 2018 Daniel Vrcic <dvrcic@srce.hr> - 0.1.0-2%{?dist}
- added Logger definition in puppet update-userdb
* Mon Jun 4 2018 Daniel Vrcic <dvrcic@srce.hr> - 0.1.0-1%{?dist}
- first release
