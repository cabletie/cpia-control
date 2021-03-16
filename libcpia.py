###########################################################################
#
# $Id: libcpia.py,v 1.1 2002/10/13 17:05:47 duncan_haldane Exp $
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
#    class status - camera status as defined by the proc-interface
#
# scan_proc
# update
# get_value
# get_keys
# set_value
# save
# load
#
###########################################################################

###########################################################################
#
# imported modules
#
###########################################################################

import re
import string
import os
import time


###########################################################################
#
# global variables
#
###########################################################################

OPEN_ERROR='open_error'


######################################################################
class status:
######################################################################

######################################################################
    def __init__(self, fname=''):

        self.camera_status={}
        self.camera_status_changed={}
        self.camera_status_mode={}
        self.camera_status_min={}
        self.camera_status_max={}
        self.camera_status_default={}

        self.fname='/proc/cpia/video0'
        self.last_update=0
        self.debug=0
        self.update_frequency=1.0

        if fname=='':
            self.scan_proc('/proc/cpia/')
        else:
            self.fname=fname
        self.init_camera_status()
        self.__update()

######################################################################
    def init_camera_status(self):
        self.camera_status={}
        self.camera_status_mode={}
        self.camera_status_min={}
        self.camera_status_max={}
        self.camera_status_default={}

######################################################################
    def scan_proc(self, proc_dir):
        try:
            for f in os.listdir(proc_dir):
                m=re.match("video\d+", f)
                if not m:
                    continue
                else:
                    self.fname=proc_dir+f
                    break
        except os.error:
            self.fname='/proc/cpia/video0'

######################################################################
    def __update(self, force=0):
        "Update the camera state."
        ""

        global OPEN_ERROR
        
        # we update only once per update_frequency
        now=time.time()
        if now-self.last_update<self.update_frequency and force==0:
            return
        self.last_update=now
        try:
            f=open(self.fname, 'r')
        except IOError:
            raise OPEN_ERROR, self.fname
        else:
            for key in self.camera_status_changed.keys():
                self.camera_status_changed[key]=0
            line=f.readline()           # 'read-only'
            mode=0                      # 0-read / 1-read/write
            match_string="([ \S]+):\s+([\S]+)*"
            while line!='':             #    driver versions
                line=f.readline()
                if line=='read-write\n':
                    mode=1
                    continue
                if mode:
                    m=re.match(match_string, line)
                else:
                    m=re.match("([ \S]+):\s+([ \S]+)", line)
                if not m:
                    m=re.match("compression_mode:", line) # compatibility hack :(
                    if not m:
                        continue
                    m=re.match("([ \S]+):\s+([\S]+)", line)
                key=m.group(1)
                if mode==1:
                    self.camera_status_mode[key]=1
                    try:
                        old_value=self.camera_status[key]
                        if old_value!=m.group(2):
                            self.camera_status[key]=m.group(2)
                            self.camera_status_changed[key]=1
                    except KeyError:
                        self.camera_status_changed[key]=0
                        self.camera_status[key]=m.group(2)
                        try:
                            self.camera_status_min[key]=m.group(3)
                            self.camera_status_max[key]=m.group(4)
                            self.camera_status_default[key]=m.group(5)
                        except:
                            pass
                else:
                    if key=='V4L Driver version':
                        match_string=\
                           "([ \S]+):\s+([\S]+)\s+([\S]+)\s+([\S]+)\s+([\S]+)"
                    self.camera_status_mode[key]=0
                    rest=m.group(2)
                    self.camera_status[key]=rest
            f.close()
                    
######################################################################
    def get_value(self, key):
        "Get the value of a key."

        self.__update()
        try:
            if self.debug:
                print "get_value key/value: '"+key+"' / '"+\
                      self.camera_status[key]+"'"
            return self.camera_status[key]
        except KeyError:
            return ''
    
######################################################################
    def get_values(self, key):
        "Get all values [current, min, max, default] of a key."

        self.__update()
        try:
            return [self.camera_status[key],
                    self.camera_status_min[key],
                    self.camera_status_max[key],
                    self.camera_status_default[key]]
        except KeyError:
            return []
    
######################################################################
    def get_keys(self):
        "Get a list of all camera keys."

        self.__update()
        return self.camera_status.keys()

######################################################################
    def get_keys_rw(self):
        "Get a list of all camera keys that can be written back."

        self.__update()
        return filter(lambda x, m=self.camera_status_mode: m[x],
                      self.camera_status.keys() )

######################################################################
    def get_changed_keys(self):
        "Get a list of all camera keys that have been changed during"
        "the last update."

        self.__update()
        return filter(lambda x, m=self.camera_status_changed: m[x],
                      self.camera_status_changed.keys() )

######################################################################
    def set_value(self, key, value):
        "Update camera value."

        if self.debug:
            print "set_value key/value: '"+key+"' / '"+value+"'"
        if self.camera_status[key]==value:
            return
        try:
            f=open(self.fname, 'w')
        except IOError:
            pass
        else:
            self.__update()
            try:
                key=key+':'
                text=string.ljust(key,25)+string.rjust(value,7)+'\n'
                f.write(text)
                f.close()
            except IOError:
                pass

######################################################################
    def load(self, fname):
        "Load the camera state from a file."

        camera=status(fname)
        for key in camera.get_keys():
            self.set_value(key, camera.get_value(key))
        return 0

######################################################################
    def save(self, fname):
        "Save the camera state to a file."

        retval=-1
        try:
            f=open(fname, 'w')
        except IOError:
            pass
        else:
            
            try:
                for key in self.get_keys_rw():
                    value=self.camera_status[key]
                    key=key+':'
                    text=string.ljust(key,25)+string.rjust(value,7)+'\n'
                    f.write(text)
            except IOError:
                retval=-1
            f.close()
            retval=0
        return retval
