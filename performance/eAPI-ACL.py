#!/usr/bin/env python
# Copyright (c) 2018 Arista Networks, Inc.  All rights reserved.
# Arista Networks, Inc. Confidential and Proprietary.

#This script is used as the basis of comparing eAPI with ACLerate.
#Thereofore, it processes the ACLs defined in exactly the same JSON files
#that ACLerate uses.  After processing these, it uses eAPI to send the
#commands to the switch, timing how long it takes for the ACL to be
#programmed.

import json
import sys
import time
from jsonrpclib import Server

#Use same config file as ACLerate so exactly same ACL and rules programmed.
ACLerate_config_file = '/mnt/flash/ACLerate-config.json'

def main():

    #Run script locally rather than remotely to make comparison fairer
    switch = Server("unix:/var/run/command-api.sock")

    #Use the same config file used as ACLerate 
    try:
        with open(ACLerate_config_file) as acl_config_file:
            acl_config_list = json.load(acl_config_file)
    except IOError:
        sys.stderr.write("Cannot open %s\n" % ACLerate_config_file)
        return

    for acl_config in acl_config_list:

        command = acl_config.get("command")
        name = acl_config.get("name")
        acl_type = acl_config.get("type")
        interface = acl_config.get("interface")
        operation = acl_config.get("operation")
        direction = acl_config.get("direction")
        rules_file = acl_config.get("rules")
        counting = acl_config.get("counting")
        #Simply doing some testing so need to sanity check these values

        if command.lower() == "delete-acl":
            sys.stderr.write("About to delete ACL %s\n" % name)
            response = switch.runCmds( 1,[ "enable", "configure", "no ip access-list " + name])
            print response
            continue

        if rules_file is None:
            sys.stderr.write("Need to add/remove rules but no rule info file specified\n")
            continue
          
        #Read in information on rules from JSON file.
        try:
            with open(rules_file) as rule_listing_file:    
                rule_list = json.load(rule_listing_file)    
        except IOError:
            sys.stderr.write("Cannot open %s\n" % rules_file)
            continue

        #List to hold the configs for each rule.
        #Thus array could end up with multiple thousand elements.
        rules_cmd_list = []
        
        #Now iterate over all rules
        for index, rule in enumerate(rule_list):
            number = rule.get("number")
            source = rule.get("source")
            destination = rule.get("destination")
            protocol = rule.get("protocol")
            action = rule.get("action")
            log = rule.get("log")
            #Simply doing some testing so need to sanity check these values

            #Compose the config for this rule and append to rules list
            rule_cmd = "%d %s ip host %s any log" % (number, action, source)
            rules_cmd_list.append(rule_cmd)

        #Time stamp before communicating with switch    
        send_commands = time.time()

        #Now send command to create ACL followed by all the rule commands to the switch
        response = switch.runCmds( 1, ["enable", "configure", "ip access-list " + name] + rules_cmd_list)
        print response
        
        #Now send command to apply ACL to interface
        response = switch.runCmds( 1, ["enable", "configure", "interface " + interface,
                                       "ip access-group " + name + " " + direction])
        print response

        #Re-visit......
        #Error check response?  (Currently verifying success using show commands.)
        #Basically assuming these are commands are synchronous?  Need to verify
        #guarantees made by runCmds()

        #Time stamp after switch responds
        received_response = time.time()

        elapsed_time = received_response - send_commands
        sys.stderr.write("Overall time is %s\n" % elapsed_time)

if __name__ == '__main__':
   sys.exit( main() )
