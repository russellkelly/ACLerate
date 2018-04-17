#!/usr/bin/env python
# Copyright (c) 2018 Arista Networks, Inc.  All rights reserved.
# Arista Networks, Inc. Confidential and Proprietary.

#This script is used experiment with and test the fcntl.flock() APIs

import fcntl
import time
import subprocess
import syslog

ACLerate_config_file = '/mnt/flash/ACLerate-config.json'

print "Opening & locking file\n"
syslog.syslog("------------------Attempting to open and lock %s--------------------" % ACLerate_config_file)
acl_config_file = open(ACLerate_config_file)

try:
    fcntl.flock(acl_config_file, fcntl.LOCK_EX | fcntl.LOCK_NB)
except IOError:
    print "Could not lock file"
    syslog.syslog("Could not lock file")

duration = 2
print "About to sleep"
syslog.syslog("About to sleep for %ss" % duration)
time.sleep(duration)

#Verify that ACLerate cannot process the config file following this update since it is locked.
print "Copy file then sleep\n"
syslog.syslog("About to copy file")
subprocess.call("cp /mnt/flash/ACLerate-config-add.json /mnt/flash/ACLerate-config.json", shell=True)

duration = 30
syslog.syslog("File copied, now sleep for %ss" % duration)
time.sleep(duration)

#Verify that ACLerate can now process the config file after it is unlocked.
print "Now unlock\n"
syslog.syslog("About to unlock file")
fcntl.flock(acl_config_file, fcntl.LOCK_UN)

