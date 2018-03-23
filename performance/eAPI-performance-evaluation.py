#!/usr/bin/env python
# Copyright (c) 2018 Arista Networks, Inc.  All rights reserved.
# Arista Networks, Inc. Confidential and Proprietary.

#This script is used to evaluate the performance of eAPI-ACL.py, which uses eAPI
#to attempt to create the specified ACL on the switch.
#It is executed:
#   eAPI-performance-evaluation.py <rule_min> <rule_max> <rule_step> <run_count>
#where
#   rule_min: lowest number of rules
#   rule_max: highest number of rules
#   rule_step: increment step size
#   run_count: number of runs for each number of rules (average of these results should be used)
#Hence
#   eAPI-performance-evaluation.py 2000 5000 500 100
#will evaluate eAPI-ACL.py's perfromance in creating ACLs containing
#2000, 2500, 3000 .... 5000 rules.  For each value in this range
#eAPI-ACL.py will be launched to try to apply the ACL 100 different
#times.  (The results are printed to eAPI-results.txt by eAPI-ACL.py.)

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

#Ensure clean slate before starting test by deleting an any pre-exsiting ACLs
subprocess.call("cp /mnt/flash/ACLerate-config-del.json /mnt/flash/ACLerate-config.json", shell=True)
subprocess.call("python /mnt/flash/eAPI-ACL.py", shell=True)

for i in xrange(rule_min, rule_max, rule_step):

    #Create rules files containing this number of rules
    #Add some randomisation to rules???
    subprocess.call("python /mnt/flash/rules-json-writer.py %s" % i, shell=True)

    #For each number of rules, the configuration file is changed to add
    #the ACL and then remove the ACL. Each time, eAPI.py is launched to
    #update the HW accordingly
    for j in range (run_count):

        #Set config file to add ACL then call eAPI to execute
        subprocess.call("cp /mnt/flash/ACLerate-config-add.json /mnt/flash/ACLerate-config.json", shell=True)
        subprocess.call("python /mnt/flash/eAPI-ACL.py", shell=True)

        #Tidy up: set config file to delete ACL then call eAPI to execute
        subprocess.call("cp /mnt/flash/ACLerate-config-del.json /mnt/flash/ACLerate-config.json", shell=True)
        subprocess.call("python /mnt/flash/eAPI-ACL.py", shell=True)

#This value is of no great signficance but print anyway.
test_duration = time.time() - start_time
sys.stderr.write("Test complete (duration: %ss)\n" % test_duration)
