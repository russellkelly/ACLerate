#!/usr/bin/env python
# Copyright (c) 2018 Arista Networks, Inc.  All rights reserved.
# Arista Networks, Inc. Confidential and Proprietary.

#This script is used to generate a an exemplar rules description
#JSON file with potentially thousands of rules for testing ACLerate.
#The number of rules is passed in as the argument.

import json
import netaddr
import sys

#Rule count input as argument
rule_count = int(sys.argv[1])

#Arbitrary initial source and destination addresses
base_src_ip_addr = 3232235777 #192.168.1.1
base_dest_ip_addr = 2808220394 #167.98.10.234

#Populate list of rules
rules = []
for j in range (rule_count):
    rule = {}
    rule["number"] = j+1
    rule["source"] = str(netaddr.IPAddress(base_src_ip_addr + j))
    rule["destination"] = str(netaddr.IPAddress(base_dest_ip_addr - j))
    rule["action"] = "permit"
    rule["protocol"] = "TCP"
    rule["log"] = "true"

    #Rules used for initial testing similar to
    #"2 permit TCP host 192.168.1.2 host 167.98.10.233 log"

    rules.append(rule)

#Convert to JSON and print to file
indented_json = json.dumps(rules, indent=2)

with open('ACLerate-rules.json', 'w') as f:
    print >> f, indented_json 
