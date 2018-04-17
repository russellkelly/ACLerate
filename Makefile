.PHONY: all rpm swix clean build sdist rpmcommon

TOPDIR = $(shell pwd)
SRCDIR = $(shell pwd)
BLDDIR=./tmp

NAME := ACLerate
VERSION := 0.5.0
RPMRELEASE := 1
PYTHON_VERSION := 2.7
PYTHON := python$(PYTHON_VERSION)

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

rpm: $(EOSRPM)

swix: $(SWIX)

$(SWIX): $(EOSRPM) manifest.txt
	$(ZIP) $@ $^

manifest.txt:
	set -e; { \
          echo 'format: 1'; \
          echo 'primaryRpm: $(EOSRPM)'; \
          echo -n '$(EOSRPM)-sha1: '; \
          set `$(SHA1SUM) "$(EOSRPM)"`; \
          echo $$1; \
        } >$@-t
	mv $@-t $@

build:
	$(PYTHON) -m compileall -q $(SRCDIR)

sdist: build doc
	$(MKDIR_P) $(BLDDIR)/build/$(BASENAME)
	cp -r ./src/* $(BLDDIR)/build/$(BASENAME)
	cp ./doc/README.pdf ./LICENSE $(BLDDIR)/build/$(BASENAME)
	cp ./SysdbMountProfiles/ACLerate $(BLDDIR)/build/$(BASENAME)
	tar -czf $(BASENAME).tar.gz -C $(BLDDIR)/build $(BASENAME)/
	$(MKDIR_P) ./dist
	mv $(BASENAME).tar.gz ./dist

rpmcommon: sdist
	$(MKDIR_P) rpmbuild
	sed -e 's#^Version:.*#Version: $(VERSION)#' \
	    -e 's#^Release:.*#Release: $(RPMRELEASE)#' $(RPMSPEC) > rpmbuild/$(NAME).spec

$(EOSRPM): rpmcommon
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
	rm -f manifest.txt $(SWIX) $(EOSRPM)
	@echo "Cleaning up byte compiled python..."
	find . -type f -regex ".*\.py[co]$$" -delete

