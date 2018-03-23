#!/usr/bin/env python
# Copyright (c) 2018 Arista Networks, Inc.  All rights reserved.
# Arista Networks, Inc. Confidential and Proprietary.

#ACLerate leverages EOS SDK to allow ACLs with thousands of rules to be programmed
#more quickly and efficiently than would typically be possible using CLI or eAPI.
#The ACL is described in JSON files which ACLerate processes and then subsequently
#invoke the appropriate EOS SDK APIs to create, update or delete the ACL.

import sys
import syslog
import eossdk
import json
import pyinotify
import functools
import time

ACLerate_config_file = '/mnt/flash/ACLerate-config.json'

# Validate the info supplied for a rule.  Specifically, a source or destination
# must be specified.  Also, there must be an action and it can be only either
# "permit" or "deny"
def rule_validate(number, source, destination, action):

    #Either a source or a destination must be specified
    if source is None and destination is None:
        sys.stderr.write("Either source or destination essential for rule\n")
        return False

    #Action must exist and must be either "permit" or "deny"
    if action is None:
        sys.stderr.write("Action is essential for rule\n")
        return False

    if action.lower() != "permit" and action.lower() != "deny" :
        sys.stderr.write("Action must be 'permit' or 'deny', i.e. not '%s'\n" % action)
        return False        

    return True

# Validate info supplied for the ACL. Specifically, must specify name, interface,
# direction and type. default_command and counting are optional with defaults of
# deny and false respectively.
def acl_validate(command, name, acl_type, direction, counting):

    #A name must be supplied
    if name is None:
        sys.stderr.write("A name must be supplied for the ACL\n")
        return False

    #Verify that name contains no invalid characters.  Note that this test  
    #is not exhaustive; simply testing potentially 'popular' illegal characters
    illegal_chars = [" ", ".", "/"]
    for char in illegal_chars:
        if char in name:
            sys.stderr.write("ACL name %s contains invalid character: %s\n" % (name, char))
            return False

    #Now process the command
    if command is None:
        sys.stderr.write("An command must be specified\n")
        return False

    valid_commands = ["add-rule", "delete-rule", "delete-acl"]
    if not (command.lower() in valid_commands): 
          sys.stderr.write("'%s' is not a valid command\n" % command)
          return False

    #A type must be specified
    if acl_type is None:
        sys.stderr.write("A type must be supplied for the ACL\n")
        return False

    valid_types = ["ipv4", "ipv6", "mac"]
    if not (acl_type.lower() in valid_types):
        sys.stderr.write("Direction must be 'IPv4', 'IPv6' or 'MAC', i.e. not '%s'\n" % acl_type)
        return False
    
    return True


# Validate supplied protocol for IP or Ethernet and supply corresponding
# protocol number/Ethertype
def protocol_validate(protocol, acl_type):
    
    protocols_ip = {"ICMP": 1,
                    "IGMP": 2,
                    "IP": 4,
                    "TCP": 6,
                    "UDP": 17,
                    "GRE": 47,
                    "ESP": 50,
                    "OSPF": 89,
                    "PIM": 103,
                    "VRRP": 112}

    protocols_eth = {"ARP": 0x806,
                     "IPV4": 0x800,
                     "IPV6": 0x86DD,
                     "LLDP": 0x88CC}
                     
    if acl_type is eossdk.ACL_TYPE_IPV4 or acl_type is eossdk.ACL_TYPE_IPV6:
        protocol_number = protocols_ip.get(protocol.upper())
        if protocol_number:
            return protocol_number
        else:
            sys.stderr.write("Protocol '%s' unsupported for IPv4/IPv6\n" % protocol)
            return None

    if acl_type is eossdk.ACL_TYPE_ETH:
        protocol_number = protocols_eth.get(protocol.upper())
        if protocol_number:
            return protocol_number
        else:
            sys.stderr.write("Protocol '%s' unsupported for Ethernet\n" % protocol)
            return None

    return None


# Previously verified that ACL type is "IPv4", IPv6" or "MAC".  Now return
# corresponding SDK type.
def acl_type_convert(acl_type):
    
    if acl_type.lower() == "ipv4":
        return eossdk.ACL_TYPE_IPV4

    if acl_type.lower() == "ipv6":
        return eossdk.ACL_TYPE_IPV6

    if acl_type.lower() == "mac":
        return eossdk.ACL_TYPE_ETH
    
    return None


# Previously verified that direction is "in" or "out".  Now return
# corresponding SDK type.
def direction_convert(direction):
    
    if direction.lower() == "in":
        return eossdk.ACL_IN

    if direction.lower() == "out":
        return eossdk.ACL_OUT

    return None

# Class for handling inotify events.
# The different event handlers will be called when the file being watched,
# the ACLerate configuration file (/mnt/flash/ACLerate-config.json), changes
# on the disk.  Respond to this file's modification or creation by
# calling the function to process its content.
class InotifyHandler(pyinotify.ProcessEvent):
   parent = None

   def my_init(self, parent):
      self.parent = parent

   def process_IN_MODIFY(self, event):
       sys.stderr.write("Processing %s which has just been modified\n" % ACLerate_config_file)
       self.parent.process_config()

   def process_IN_CREATE(self, event):
       sys.stderr.write("Processing %s which has just been created\n" % ACLerate_config_file)
       self.parent.process_config()

   def process_IN_DELETE(self, event):
       sys.stderr.write("ACLerate config file, %s, deleted\n" % ACLerate_config_file)
    
# Main ACLerate class.  Has functions to carry out EOS SDK and inotify initialisations,
# process configuration and rules description files, invoke the appropriate EOS SDK
# ACL APIs and handle pertinent updates from Sysdb via EOS SDK.
class ACLerate(eossdk.AgentHandler, eossdk.AclHandler,
               eossdk.IntfHandler, eossdk.FdHandler):
    
   def __init__(self, sdk):
      #Carry out SDK-specific initialisation 
      sys.stderr.write("Entering __init__()\n")
      agent_mgr = sdk.get_agent_mgr()
      acl_mgr = sdk.get_acl_mgr()
      intf_mgr = sdk.get_intf_mgr()
      self.agent_mgr = agent_mgr
      self.acl_mgr = acl_mgr
      self.intf_mgr = intf_mgr
      eossdk.AgentHandler.__init__(self, agent_mgr)
      eossdk.AclHandler.__init__(self, acl_mgr)
      eossdk.IntfHandler.__init__(self, intf_mgr)
      eossdk.FdHandler.__init__(self)
      self.tracer = eossdk.Tracer("ACLeratePythonAgent")
      syslog.syslog("ACLerate Python Agent - init")
      self.tracer.trace0("Python agent constructed")

      #Now register with inotify to receive be notified of changes to the config file
      self.config_file = ACLerate_config_file
      self.wm = pyinotify.WatchManager()
      handler = functools.partial(InotifyHandler, parent=self)
      mask = pyinotify.IN_MODIFY | pyinotify.IN_CREATE | pyinotify.IN_DELETE
      self.wm.watch_transient_file(ACLerate_config_file, mask, handler)
      self.inotifier = pyinotify.AsyncNotifier(self.wm,
                                              InotifyHandler(parent=self))
      self.inotifier.coalesce_events(True)
      self.inotify_fd = self.wm.get_fd()
      self.watch_readable(self.inotify_fd, True)

   def on_initialized(self):
      self.tracer.trace0("Initialised")
      syslog.syslog("ACLerate Python Agent Initialized")
      self.agent_mgr.status_set("Status:", "Administratively Up")
      self.watch_all_acls(True)
      self.process_config()

   # Critical function; processes configuration and rules description files.
   # Called whenever inotify indicates the configuration file has changed on disk.
   def process_config(self):
      self.tracer.trace0("Processing config")
      syslog.syslog("ACLerate Python Agent Processing config")

      #Being conservative with ACLerate's performance evaluation
      #since including the time to process the JSON files in the ACL
      #processing time by timestamping here.  Should really
      #start the measurement from when the ACL info sent to SDK.
      #But better to under-promise.....
      start_time = time.time()
      self.start_time = start_time
      
      #Attempt to parse ACLerate_config_file 
      try:
          with open(self.config_file) as acl_config_file:
              acl_config_list = json.load(acl_config_file)
      except IOError:
          sys.stderr.write("Cannot open %s\n" % self.config_file)
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

          #Sanity check ACL parameters (before potentially
          #iterating over thousands of rules!).  If invalid, skip
          #processing rest of this ACL and continue to next ACL
          if not acl_validate(command, name, acl_type, direction, counting):
              sys.stderr.write("Invalid ACL input data\n")
              continue

          #Convert external ACL type to SDK's type
          sdk_type = acl_type_convert(acl_type)
          if sdk_type is None:
              sys.stderr.write("Invalid ACL type specified\n")
              continue

          #Get handle to ACL.
          acl_key = eossdk.AclKey(str(name), sdk_type)

          #If input command is to delete the ACL, simply call the appropriate
          #SDK API and continue onto next ACL in the list.  i.e. no need to be
          #concerned with interfaces, rules etc.
          if command.lower() == "delete-acl":
              sys.stderr.write("About to delete %s ACL %s\n" % (acl_type, name))
              self.acl_mgr.acl_del(acl_key)
              #Now call commit to actually push changes to HW.
              self.acl_mgr.acl_commit()
              continue
 
          #Next, if an interface is specified, verify it actually exists
          #and correct parameters have been specified
          if interface:
              intf_id = self.interface_validate(interface, operation, direction)
              if intf_id:
                  #Convert external direction to SDK's type
                  sdk_direction = direction_convert(direction)
                  if sdk_direction is None:
                      sys.stderr.write("Invalid direction specified\n")
                      continue
              else:
                  sys.stderr.write("Invalid ACL interface input data\n")
                  continue

          #Set ACL counting behaviour if specified.  If not, will
          #simply fallback to default ACL behaviour.
          if counting:
              if counting.lower() == "true":
                  self.acl_mgr.acl_counters_enabled_set(acl_key, True)
              if counting.lower() == "false":
                  self.acl_mgr.acl_counters_enabled_set(acl_key, False)

          #Rules files is needed.  Does it actually exist?
          #Is a comprehensive unwind needed in the error case?
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

          #Now iterate over all rules
          for index, rule in enumerate(rule_list):
              number = rule.get("number")
              source = rule.get("source")
              destination = rule.get("destination")
              protocol = rule.get("protocol")
              action = rule.get("action")
              log = rule.get("log")

              #Rule must have a sequence number.
              if number is None:
                  sys.stderr.write("Number is essential for rule\n")
                  continue
    
              #If input command is to delete the rule, simply call the SDK API
              #and continue to next rule in the list.
              #i.e. no need to be concerned with addresses, protocols etc.
              if command.lower() == "delete-rule":
                  self.acl_mgr.acl_rule_del(acl_key, int(number))
                  continue

              #If here, then the command must be to add rule.
              #So verify if rule data supplied is valid.
              if rule_validate(number, source, destination, action) == False:
                  sys.stderr.write("Invalid rule input data\n")
                  continue

              #Create IP ACL rule object.  Used for IPv4 and IPv6 ACLs but
              #different object needed for Ethernet ACLs.
              #(Perhaps create object with all rule info and invoke
              #functions to process for ACL, IPv4, IPv6 etc?
              #Needs more thought on optimal way to handle different ACL type)
              acl_rule = eossdk.AclRuleIp()

              #Now parse the rule data and invoke appropriate SDK
              #APIs to create requisite data structures.
              if source:
                  try:
                      #How is "any" handled? 0.0.0.0/0?
                      if source == "any":
                          source = "0.0.0.0/0"

                      #String to IP address conversion of source?    
                      sdk_prefix = eossdk.IpPrefix(str(source))
                      sdk_addr = eossdk.IpAddrMask(sdk_prefix.network(),
                                                       sdk_prefix.prefix_length())
                      acl_rule.source_addr_is(sdk_addr)
                  except eossdk.Error:
                      sys.stderr.write("Error processing source address %s\n" % source)
                      continue

              if destination:
                  try:
                      #How is "any" handled? 0.0.0.0/0?
                      if destination == "any":
                          destination = "0.0.0.0/0"

                      #String to IP address conversion of destination?    
                      sdk_prefix = eossdk.IpPrefix(str(destination))
                      sdk_addr = eossdk.IpAddrMask(sdk_prefix.network(),
                                                       sdk_prefix.prefix_length())
                      acl_rule.destination_addr_is(sdk_addr)
                  except eossdk.Error:
                      sys.stderr.write("Error processing destination address %s\n" % destination)
                      continue

              if protocol:
                  protocol_number = protocol_validate(protocol, sdk_type)
                  if protocol_number:
                      acl_rule.ip_protocol_is(protocol_number)
                  else:
                      sys.stderr.write("Error processing protocol %s\n" % protocol)
                      continue

              #Previously verified that action is 'permit' or 'deny'    
              if action:
                  try:
                      if action.lower() == "permit":
                          acl_rule.action_is(eossdk.ACL_PERMIT)
                      else:
                          acl_rule.action_is(eossdk.ACL_DENY)
                  except:
                      sys.stderr.write("Error processing action %s\n" % action)
                      continue

              if log:
                  try:
                      if log.lower() == "true":
                          acl_rule.log_is(True)
                      else:
                          acl_rule.log_is(False)
                  except:
                      sys.stderr.write("Error processing log %s\n" % log)
                      continue
 
              #Now add this rule to ACL, with appropriate sequence number
              #Should only ever be here when adding rules.... paranoid check.
              if command.lower() == "add-rule":
                  self.acl_mgr.acl_rule_set(acl_key, int(number), acl_rule)

          parsing_time = time.time()
          self.parsing_time = parsing_time

          self.rule_count = index+1

          #Now call commit to actually push changes to HW.
          self.acl_mgr.acl_commit()

          #Should ACL be attached or detached from interface?
          if intf_id:
              if operation.lower() == "attach":                 
                  self.acl_mgr.acl_apply(acl_key, intf_id, sdk_direction, True)
              if operation.lower() == "detach":                 
                  self.acl_mgr.acl_apply(acl_key, intf_id, sdk_direction, False)

          self.parsing_duration = parsing_time - start_time

          sys.stderr.write("Time to parse config files for ACL %s is %s\n" % (name, self.parsing_duration))

   # An interface has been specified so verify that it exists and is usable.
   # Also check that the accompanying parameters are valid.  If both true then
   # the ACL can be attached/detached from the interface so return the 
   # interface id.  If not, return None so processing stops before attempting
   # to process the potentially large rules description file.
   def interface_validate(self, interface, operation, direction):
       
       #Verify interface exists
       try:
           intf_id = eossdk.IntfId(str(interface))
       except eossdk.NoSuchInterfaceError:
           sys.stderr.write("Interface %s does not exist\n" % interface)
           return None
 
       if direction.lower() != "in" and direction.lower() != "out" :
           sys.stderr.write("Direction must be 'in' or 'out', i.e. not '%s'\n" % direction)
           return None

       if operation.lower() != "attach" and operation.lower() != "detach" :
           sys.stderr.write("Operation must be 'attach' or 'detach', i.e. not '%s'\n" % operation)
           return None

       return intf_id

   # Called when file descriptor number is readable
   def on_readable(self, fd): 
       if fd == self.inotify_fd:
           self.inotifier.handle_read()
           
   # Called upon hardware successfully committing all pending transactions.
   def on_acl_sync(self):
       self.sync_time = time.time()

       sys.stderr.write("Number of rules is %s\n" % str(self.rule_count))

       #Need to be careful of timestamping here when there are multiple ACLs etc
       #Should perhaps verify the ACL name in question?  Remove before production.
       hw_processing_duration = self.sync_time - self.parsing_time
       sys.stderr.write("HW processing duration is is %s\n" % hw_processing_duration)

       overall_duration = self.sync_time - self.start_time
       sys.stderr.write("Overall duration is %s\n" % overall_duration)

       #Now print append to file; delimiters "," for easy Excel processing.
       #Used for performance evaluation; remove before production.
       results = "%d, %s, %s, %s\n" % (self.rule_count, self.parsing_duration, hw_processing_duration, overall_duration)
       f = open('/mnt/flash/ACLerate-results.txt', 'a+')
       f.write(results)

   # Called if a problem stopped ACL configuration from being committed.
   # e.g. because the TCAM is full
   def on_acl_sync_fail(self, linecard, message):
       sys.stderr.write("Failure applying ACL to HW: %s, %s\n" % (linecard, message))

      
def main():
    sdk = eossdk.Sdk()
    ACLerator = ACLerate(sdk)
    sdk.main_loop(sys.argv)

if __name__ == '__main__':
   sys.exit( main() )
