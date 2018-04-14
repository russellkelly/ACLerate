%{!?python_sitelib: %define python_sitelib %(%{__python} -c "from distutils.sysconfig import get_python_lib; print get_python_lib()")}

Name:    ACLerate
Version: Replaced_by_make
Release: 1%{?dist}
Summary: Arista EOS SDK agent to program large ACLs quickly and efficiently
Source:  %{name}-%{version}-%{release}.tar.gz
Group:   Applications/Internet
License: BSD-3-Clause
URL:     http://www.arista.com

%global ACLerate_root /opt/%{name}
%global sysdbprofile_root /usr/lib/SysdbMountProfiles

#BuildRoot: %{_tmppath}/%{name}-%{version}-%{release}-root-%(%{__id_u} -n)
BuildArch: noarch
Requires:  python2
Requires:  python2-pam
Requires:  Eos-release
#Requires:  nginx
#Requires:  uwsgi
#Requires:  Eos-release >= 2:4.14.5

%description
Arista EOS SDK agent to program large ACLs quickly and efficiently

%prep
%setup -q -n %{name}-%{version}-%{release}

%install
%{__rm} -rf %{buildroot}
%{__install} -m 0644 ACLerate %{buildroot}%{ACLerate_root}/SysdbProfiles/ACLerate
%{__install} -m 0644 ACLerate.pyc %{buildroot}%{python_sitelib}/ACLerate.pyc
%{__install} -m 0755 src %{buildroot}%{ACLerate_root}/src
%{__install} -m 0644 README.pdf %{buildroot}%{ACLerate_root}/doc/README.pdf
%{__install} -m 0644 LICENSE %{buildroot}%{ACLerate_root}/doc/LICENSE


%clean
%{__rm} -rf %{buildroot}

%post
# 1 - Perform tasks related to initial install
# 2 - Perform tasks related to upgrade (existing to new one)
if [ $1 -eq 1 ]; then
    if [ -d "%{sysdbprofile_root}" ]; then
        %{__cp} %{ACLerate_root}/SysdbProfiles/ACLerate %{sysdbprofile_root}/ACLerate
    fi
fi
exit 0

# When the Cli package is available, install the daemon config command
%triggerin -- Cli
# if sysdb profiles exist
if [ -d "%{sysdbprofile_root}" ]; then
    FastCli -p 15 -c "configure
    daemon %{name}
    exec /usr/bin/ACLerate 
    no shutdown
    end"
else
    FastCli -p 15 -c "configure
    daemon %{name}
    exec /usr/bin/ACLerate
    no shutdown
    end"
fi
exit 0


%preun
# 0 - Perform tasks related to uninstallation
# 1 - Perform tasks related to upgrade
if [ $1 -eq 0 ]; then
    if [ -f "%{sysdbprofile_root}/ACLerate" ]; then
        %{__rm} %{sysdbprofile_root}/ACLerate
    fi
fi
exit 0


%files
%defattr(-,root,eosadmin,-)
%{python_sitelib}/ACLerate.pyc
%dir /persist/sys/%{name}
%dir %{ACLerate_root}
%{_bindir}/ACLerate
%{ACLerate_root}/bin
%{ACLerate_root}/SysdbProfiles
%dir %{ACLerate_root}/doc
%docdir %{ACLerate_root}/doc
%doc %{ACLerate_root}/doc/README.pdf
%license %{ACLerate_root}/doc/LICENSE

%changelog
* Fri Apr 13 2018 Olufemi Komolafe<femi@arista.com> - %{version}-1
- Initial RPM build
