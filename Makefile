###########################################################################
#
# $Id: Makefile,v 1.2 2002/10/13 17:15:09 duncan_haldane Exp $        
#
# Copyright (C) 2000, Peter Pregler (Peter_Pregler@email.com)
#                     
###########################################################################
#
#  $Revision: 1.2 $
#  $Date: 2002/10/13 17:15:09 $
#  $Author: duncan_haldane $
#  Created by: Peter Pregler.
#
###########################################################################
#
# Description:
#    Global Makefile for project cpia-control program
#
# Targets:
# - all: default target - create all
# - lib: byte-compile stuff
# - doc: create documentation
# - install: install all necessary files
# - clean: clean for tarball
# - dist: generate tar-ball
#
# - debian: special build for debian package
# - debian_clean: clean also what is left around from debian build
#
###########################################################################

# this is for a debian linux system, set to where things go at your site
SITE_PACKAGES_DIR=${DESTDIR}/usr/lib/python2.3/site-packages
BIN_DIR=${DESTDIR}/usr/bin

###########################################################################
#
# no need to change anything below, hopefully
#
###########################################################################

PROG = cpia-control
LIBS = cpia_control.py libcpia.py
DESTDIR = ${DESTDIR:/usr/local}

CLIBS:=$(LIBS:.py=.pyc)
OLIBS:=$(LIBS:.py=.pyo)

all:	doc lib
#all:    lib

doc:	
	cd docs && ${MAKE}

lib:	$(CLIBS) ${OLIBS}

install:
	install -m 755 ${PROG} ${BIN_DIR}
	install -m 644 ${LIBS} ${SITE_PACKAGES_DIR}
	install -m 644 ${CLIBS} ${SITE_PACKAGES_DIR}
	install -m 644 ${OLIBS} ${SITE_PACKAGES_DIR}

clean:
	rm -f *.pyc *.pyo
	cd docs && ${MAKE} clean

dist:	debian_clean
	(cd ..; \
	tar --exclude=RCS --exclude=debian -cvzf cpia-control.tgz cpia-control)

###########################################################################
#
# debian specific targets, make no sense for normal users
#
###########################################################################

debian:	all
	cp docs/cpia-control.man  debian/cpia-control.1

debian_clean:	clean
	rm -f build-stamp
	rm -f debian/cpia-control.1

###########################################################################
#
# aparently GNU-tar does not support python
#
###########################################################################

%.pyc:%.py;
	@echo -n 'compiling $@: '
	@python -c "import py_compile; py_compile.compile('$<')"
	@echo 'done'

%.pyo:%.py;
	@echo -n 'compiling $@: '
	@python -O -c "import py_compile; py_compile.compile('$<')"
	@echo 'done'
