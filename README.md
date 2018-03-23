# ACLerate
EOS SDK agent to program ACLs with thousands of rules quickly and efficiently


Applying an ACL that contains thousands of rules to a switch via the CLI or eAPI may be impractical due to the excessive time taken to process the ACL.  ACLerate aims to provide a solution to this problem by leveraging EOS SDK to allow large ACLs to be programmed more quickly and efficiently.

ACLerate is started and stopped using the conventional CLI for executing EOS SDK daemons. As shown in Figure 1, the main way the client communicates with ACLerate is via JSON files.  JSON is chosen as it is a popular, flexible and lightweight means of describing the information that is required for ACLerate to handle the client’s request.  The two types of JSON files needed are: 
* configuration file 
  * contains an array with each element corresponding to an ACL and containing information that
    * describes the ACL
    * identifies the command the client wishes to execute (e.g. to add rules, remove rules or delete the ACL)
    * specifies the interface should the client wish to attach or detach the ACL from an interface
    * points to to the rule description file, i.e. the JSON file containing information about the rules to be added, overwritten or removed from the ACL.
  * must be called ```/mnt/flash/ACLerate-config.json``` 
  * updates to this file will be automatically detected by ACLerate and will trigger it to be processed.

* rules description file
  * contains an array with potentially thousand of elements, each corresponding to a rule and containing information that:
    * describes the rule in question (e.g. the action, sequence number, traffic characteristics to match etc)
  * must be referenced by the corresponding ACLerate configuration file, allowing the rules to be associated with an ACL.
  * may be referenced by multiple configuration files, i.e. it is legitimate for the same rules description file to be associated with different ACLs (e.g. to conveniently facilitate applying the same rules to different interfaces or directions).

ACLerate uses inotify to track any changes to the ACLerate configuration file.  Upon being notified that this file has been modified, ACLerate will parse the JSON therein and attempt to execute the command specified, accessing the rules description file as/when necessary using the data in the referenced file.

<img src="ACLerate_Overview.jpg" alt="Drawing"  height="800" width="500">
