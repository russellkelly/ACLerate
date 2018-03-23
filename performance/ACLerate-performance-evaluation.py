#!/usr/bin/env python
# Copyright (c) 2018 Arista Networks, Inc.  All rights reserved.
# Arista Networks, Inc. Confidential and Proprietary.

#This script is used to evaluate the performance of ACLerate
#It is executed:
#   ACLerate-performance-evaluation.py <rule_min> <rule_max> <rule_step> <run_count>
#where
#   rule_min: lowest number of rules
#   rule_max: highest number of rules
#   rule_step: increment step size
#   run_count: number of runs for each number of rules (average of these results should be used)
#Hence
#   ACLerate-performance-evaluation.py 2000 5000 500 100
#will evaluate ACLerate's perfromance in creating ACLs containing
#2000, 2500, 3000 .... 5000 rules.  For each value in this range
#ACLerate will attempt to apply the ACL to HW and then remove it
#100 times before moving on.
#(The results are printed to ACLerate-results.txt by ACLerate.)
#The ACLerate daemon should be running before this script is kicked off.

import json
import sys
import time
import subprocess
from jsonrpclib import Server

rule_min = int(sys.argv[1])
rule_max = int(sys.argv[2])
rule_step = int(sys.argv[3])
run_count = int(sys.argv[4])

start_time = time.time()

#Need to pause to allow the HW to apply the ACL before removing it etc.
#May need to make these larger as processing times grows with number of rules
#i.e. Care should be taken with these values.
add_processing_delay = 30
del_processing_delay = 5

#Ensure clean slate before starting test by deleting an any pre-exsiting ACLs
subprocess.call("cp /mnt/flash/ACLerate-config-del.json /mnt/flash/ACLerate-config.json", shell=True)
time.sleep(del_processing_delay)

for i in xrange(rule_min, rule_max, rule_step):

    #Create rules files containing this number of rules
    #Add some randomisation to rules???
    subprocess.call("python /mnt/flash/rules-json-writer.py %s" % i, shell=True)

    #For each number of rules, the configuration file is changed to add
    #the ACL and then remove the ACL.  These changes to the file are
    #detected by ACLerate which will then update the HW accordingly.
    for j in range (run_count):

        #Set config file to add ACL.
        subprocess.call("cp /mnt/flash/ACLerate-config-add.json /mnt/flash/ACLerate-config.json", shell=True)
        #Pause for the HW to create the ACL.
        time.sleep(add_processing_delay)

        #Tidy up: set config file to delete ACL then call eAPI to execute
        subprocess.call("cp /mnt/flash/ACLerate-config-del.json /mnt/flash/ACLerate-config.json", shell=True)
        #Pause for the HW to delete the ACL.
        time.sleep(del_processing_delay)

#This value is of no great signficance but print anyway.
test_duration = time.time() - start_time
sys.stderr.write("Test complete (duration: %ss)\n" % test_duration)
