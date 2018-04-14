.PHONY: all rpm swix clean build sdist rpmcommon

TOPDIR = $(shell pwd)
SRCDIR = $(shell pwd)
BLDDIR=./tmp

NAME := ACLerate
VERSION := 0.5.0
RPMRELEASE := 1
PYTHON_VERSION := 2.7
PYTHON := python$(PYTHON_VERSION)

PAM_VER := 1.8.2-5
PAM_RPM_NAME := python-pam-$(PAM_VER).fc24.src.rpm
PAM_EOS_RPM := python2-pam-$(PAM_VER).eos4.noarch.rpm
PAM_URL := https://dl.fedoraproject.org/pub/fedora/linux/development/rawhide/Everything/source/tree/Packages/p/

SRCDIR := $(TOPDIR)/src

# RPM build defines
RPMSPECDIR := $(TOPDIR)
RPMSPEC := $(RPMSPECDIR)/ACLerate.spec
RPM_TARGET := noarch
BASENAME := $(NAME)-$(VERSION)-$(RPMRELEASE)
EOSRPM := $(BASENAME).$(RPM_TARGET).rpm
SWIX := $(BASENAME).swix

## All markdown files in the working directory
SRC = $(wildcard *.md)
PDFS=$(SRC:.md=.pdf)

# Various commands we need.
MKDIR_P := mkdir -p
SHA1SUM := sha1sum
# 9 - slow (i.e. most) compresssion
ZIP := zip -9

all: clean swix checksum

doc: README.pdf
	mv README.pdf $(TOPDIR)/doc

%.pdf: %.md
	pandoc -o $@ $<

python2-pam: $(PAM_EOS_RPM)

rpm: $(EOSRPM)

swix: $(SWIX)

$(SWIX): $(EOSRPM) $(PAM_EOS_RPM) manifest.txt
	$(ZIP) $@ $^
	rm -f $(PAM_EOS_RPM)

manifest.txt:
	set -e; { \
          echo 'format: 1'; \
          echo 'primaryRpm: $(EOSRPM)'; \
          echo -n '$(EOSRPM)-sha1: '; \
          set `$(SHA1SUM) "$(EOSRPM)"`; \
          echo $$1; \
          echo -n '$(PAM_EOS_RPM)-sha1: '; \
          set `$(SHA1SUM) $(PAM_EOS_RPM)`; \
          echo $$1; \
        } >$@-t
	mv $@-t $@

build:
	$(PYTHON) -m compileall -q $(SRCDIR)

$(PAM_EOS_RPM):
	#wget -r -l1 -nd --no-parent -A '$(PAM_RPM_NAME).*.src.rpm' $(PAM_URL)
	mock --uniqueext=${USER} -r eos-4-i386 --no-clean --no-cleanup-after --define="%rhel 4" ./vendored/$(PAM_RPM_NAME)
	cp /var/lib/mock/eos-4-i386-${USER}/root/builddir/build/RPMS/$(PAM_EOS_RPM) .

sdist: build doc
	$(MKDIR_P) $(BLDDIR)/build/$(BASENAME)
	cp -r ./src/* $(BLDDIR)/build/$(BASENAME)
	#cp -r ./config/* $(BLDDIR)/build/$(BASENAME)
	cp ./doc/README.pdf ./LICENSE $(BLDDIR)/build/$(BASENAME)
	cp -r ./src/ACLerate.pyc $(BLDDIR)/build/$(BASENAME)
	cp ./SysdbMountProfiles/ACLerate $(BLDDIR)/build/$(BASENAME)
	tar -czf $(BASENAME).tar.gz -C $(BLDDIR)/build $(BASENAME)/
	$(MKDIR_P) ./dist
	mv $(BASENAME).tar.gz ./dist

rpmcommon: sdist
	$(MKDIR_P) rpmbuild
	sed -e 's#^Version:.*#Version: $(VERSION)#' \
	    -e 's#^Release:.*#Release: $(RPMRELEASE)#' $(RPMSPEC) > rpmbuild/$(NAME).spec

$(EOSRPM): rpmcommon
	@echo "Wine o clock..."
	@rpmbuild --define "_topdir %(pwd)/rpmbuild" \
	--define "_specdir $(RPMSPECDIR)" \
	--define "_sourcedir %(pwd)/dist/" \
	--define "_rpmdir %(pwd)" \
	--define "_srcrpmdir %{_topdir}" \
	--define "_rpmfilename %%{NAME}-%%{VERSION}-%%{RELEASE}.%%{ARCH}.rpm" \
	--define "__python /usr/bin/python" \
	-bb rpmbuild/$(NAME).spec
	@rm -f rpmbuild/$(NAME).spec

checksum:
	@sha512sum $(SWIX) > $(SWIX).sha512sum

clean:
	@echo "Cleaning up build/dist/rpmbuild..."
	rm -rf $(BLDDIR)
	rm -rf build dist rpmbuild
	rm -f manifest.txt $(SWIX) $(EOSRPM) $(PAM_EOS_RPM)
	@echo "Cleaning up byte compiled python..."
	find . -type f -regex ".*\.py[co]$$" -delete

