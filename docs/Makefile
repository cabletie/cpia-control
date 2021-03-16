##########################################################################
#
# $Id: Makefile,v 1.1 2002/10/13 17:05:47 duncan_haldane Exp $        
#
# Copyright (C) 2000, Peter Pregler (Peter_Pregler@email.com)
#                     
###########################################################################
#
#  $Revision: 1.1 $
#  $Date: 2002/10/13 17:05:47 $
#  $Author: duncan_haldane $
#  Created by: Peter Pregler.
#
###########################################################################
#
# Description:
#    Makefile for cpia-control program documentation
#
###########################################################################

%.ps:%.sgml;
	@sgmltools --backend=ps $<

%.man:%.sgml;
	@docbook-to-man $< > $@

all:	ps man

ps:	cpia-control.ps

man:	cpia-control.man

clean:
	rm -f cpia-control.ps cpia-control.man
