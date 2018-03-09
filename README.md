# PySoarLib
#### Aaron Mininger
#### 2018

This is a python library module with code to help make working with Soar SML in python 
just a little bit easier. 

## IdentifierExtensions 
These add a few helper methods to the sml.Identifier class:
(Do not need to import directly, come with any import from module)

`Identifier.GetChildString(attribute:str)`
Given an attribute, will look for a child WME of the form (<id> ^attribute <value>) and return the value as a string

`Identifier.GetChildInt(attribute:str)`
Given an attribute, will look for a child IntegerWME of the form (<id> ^attribute <value>) and return the value as an integer

`Identifier.GetChildFloat(attribute:str)`
Given an attribute, will look for a child FloatWME of the form (<id> ^attribute <value>) and return the value as an float

`Identifier.GetChildId(attribute:str)`
Given an attribute, will look for a child WME of the form (<id> ^attribute <child_id>) and return an Identifier with <child_id> as the root

`Identifier.GetAllChildIds(attribute:str=None)`
Given an attribute, returns a list of Identifiers from all child WME's matching (<id> ^attribute <child_id>)
If no attribute is specified, all child Identifiers are returned

`Identifier.GetAllChildValues(attribute:str=None)`
Given an attribute, returns a list of strings from all child WME's matching (<id> ^attribute <value>)
If no attribute is specified, all child WME values (non-identifiers) are returned

## SoarWME:
A class which can represent a WMElement with an (<id> ^att value) but takes care of actually interfacing with working memory

`SoarWME(att:str, val:any)`
Defines the wme's attribute and value
Here, if val is an int or float, it will create those specific types of elements in WM

`set_value(newval:any)`
Sets the value of the WME if different than previous value

`is_added():bool`
Returns true if the WME has been added to working memory

`add_to_wm(parent_id:Identifier)`
Adds the wme to soar's working memory

`update_wm()`
Will update the wme in soar's working memory if the value changed

`remove_from_wm()`
Will remove the wme from soar's working memory

## SVSCommands:
A collection of helper functions to create string commands that can be send to SVS
Here pos, rot, and scl are lists of 3 numbers (like [1, 2, 3])

* `add_box(obj_id, pos=None, rot=None, scl=None)`
* `change_pos(obj_id, pos)`
* `change_rot(obj_id, rot)`
* `change_scl(obj_id, scl)`
* `delete(obj_id)`
* `add_tag(obj_id, tag_name, tag_value)`
* `change_tag(obj_id, tag_name, tag_value)`
* `delete_tag(obj_id, tag_name)`

## AgentConnector
Defines an abstract base class for creating classes that connect to Soar's input/output links

`AgentConnector(agent:SoarAgent, print_handler:None)`
print_handler determines how output is printed, defaults to normal python print

`register_output_handler(command_name:str)`
Will register a handler that listens to output link commands with the given name

`on_init_soar()`
Event Handler called when init-soar happens (need to release SML working memory objects)

`on_input_phase(input_link:Identifier)`
Event Handler called every input phase

`on_output_event(att_name, root_id)`
Event Handler called when a new output link command is created `(<output-link> ^att_name <root_id>)`

## LanguageConnector
Defines a connector for putting NL messages on the agent's input-link and receiving messages from the agent

`send_message(message:str)`
Sends the given message (which should be a single English sentence) to the agent
Replaces the previous message, if there is one

`register_message_callback(agent_message_callback)`
The given callback function is called when the agent puts a message on the output-link

## SoarAgent
Defines a class used for creating a soar agent, sending commands, running it, etc.

`SoarAgent(config_file:str, print_handler=None)`
config_file must exit
print_handler specifies how output is handled (defaults to python print())

Will create the soar kernel and agent, as well as source the agent files

#### Config File Format:
* agent-name = <name>
The name of the agent to use when creating it
* agent-source = <filename>
Soar file to source containing the agent's soar code
* smem-source = <filename>
Soar file to source containing smem --add commands
* verbose = <bool>
If true, prints additional info when sourcing
* watch-level = <int>
Determines how much detail to print
* spawn-debugger = <bool> 
If true, will spawn the soar debugger
* write-to-stdout = <bool>
If true, will echo any soar output/printing to standard out
* enable-log = <bool>
If true, will write any soar output/printing to file rosie.log

`connect()`
Will register callbacks (call before running)
`disconnect()`
Will deregister callbacks
`start()`
Will cause the agent to start running in new thread (non-blocking)
`stop()`
Will stop the agent
`execute_command(cmd:str)`
Sends the given command to the agent and writes the output using print_handler
`kill()`
Will stop the agent destroy the agent/kernel
	







