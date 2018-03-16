#!/usr/bin/env python
# Copyright (c) 2018 Arista Networks, Inc.  All rights reserved.
# Arista Networks, Inc. Confidential and Proprietary.

#This script is used to generate a rules JSON description file with
#thousands of rules for testing ACLerate.

import json
import netaddr

rule_count = 2500
base_ip_address = 3232235777 #192.168.1.1
#base_ip_address = 3232267009 #192.168.123.1


#List of rules
rules = []
for j in range (rule_count):
    rule = {}
    rule["number"] = j+1
    rule["source"] = str(netaddr.IPAddress(base_ip_address + j))
    rule["action"] = "deny"
    rule["log"] = "true"

    #Simple minimalistic rules used for initial testing, e.g.
    #"2 deny ip host 192.168.1.2 any log"
    #Will be interesting to use more complex rules for
    #further testing, especially as the rule's complexity
    #apparently impacts the TCAM utilisation.

    rules.append(rule)

#Convert to JSON and print to file
indented_json = json.dumps(rules, indent=2)

with open('ACLerate-rules.json', 'w') as f:
    print >> f, indented_json 
