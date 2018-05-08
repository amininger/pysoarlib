# PySoarLib
### Aaron Mininger
#### 2018

This is a python library module with code to help make working with Soar SML in python 
just a little bit easier. 

Methods do have docstrings, to read help information open a python shell and type
```
import pysoarlib
help(pysoarlib)
help(pysoarlib.SoarAgent)
```

## IdentifierExtensions 
These add a few helper methods to the sml.Identifier class:
(Do not need to import directly, come with any import from module)

`Identifier.GetChildString(attribute:str)` 
Given an attribute, will look for a child WME of the form `(<id> ^attribute <value>)` and return the value as a string

`Identifier.GetChildInt(attribute:str)` 
Given an attribute, will look for a child IntegerWME of the form `(<id> ^attribute <value>)` and return the value as an integer

`Identifier.GetChildFloat(attribute:str)` 
Given an attribute, will look for a child FloatWME of the form `(<id> ^attribute <value>)` and return the value as an float

`Identifier.GetChildId(attribute:str)` 
Given an attribute, will look for a child WME of the form `(<id> ^attribute <child_id>)` and return an Identifier with <child_id> as the root

`Identifier.GetAllChildIds(attribute:str=None)` 
Given an attribute, returns a list of Identifiers from all child WME's matching `(<id> ^attribute <child_id>)`
If no attribute is specified, all child Identifiers are returned

`Identifier.GetAllChildValues(attribute:str=None)` 
Given an attribute, returns a list of strings from all child WME's matching `(<id> ^attribute <value>)`
If no attribute is specified, all child WME values (non-identifiers) are returned

## SoarWME:
A class which can represent a WMElement with an `(<id> ^att value)` but takes care of actually interfacing with working memory

You can update its value whenever you want, it will not affect working memory. To change working memory, call `add_to_wm`, `update_wm`, and `remove_from_wm` during an event callback (like BEFORE_INPUT_PHASE)

## SVSCommands:
A collection of helper functions to create string commands that can be send to SVS
Here pos, rot, and scl are lists of 3 numbers (like [1, 2.5, 3.1])

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

`add_output_command(command_name:str)` 
Will register a handler that listens to output link commands with the given name

`on_init_soar()` 
Event Handler called when init-soar happens (need to release SML working memory objects)

`on_input_phase(input_link:Identifier)` 
Event Handler called every input phase

`on_output_event(command_name, root_id)` 
Event Handler called when a new output link command is created `(<output-link> ^command_name <root_id>)`


## SoarAgent
Defines a class used for creating a soar agent, sending commands, running it, etc.

`SoarAgent(config_filename=None, print_handler=None, **kwargs)` 
Will create the soar kernel and agent, as well as source the agent files
print_handler specifies how output is handled (defaults to python print())
config_filename names a file with agent settings in it

#### Config Settings (kwargs)
* agent_name = [name] 
The name of the agent to use when creating it
* agent_source = [filename] 
Soar file to source containing the agent's soar code
* smem_source = [filename] 
Soar file to source containing smem --add commands
* verbose = [bool] 
If true, prints additional info when sourcing
* watch_level = [int] 
Determines how much detail to print
* spawn_debugger = [bool] 
If true, will spawn the soar debugger
* write_to_stdout = [bool] 
If true, will echo any soar output/printing via print_handler
* enable_log = [bool] 
If true, will write any soar output/printing to file agent-log.log

#### Config File
Instead of passing as arguments, you can pass in a filename as config_filename
Each line in the file should be 'setting = value'
Also, setting names use hyphens instead of underscores
Example File:
	agent-name = Rosie
	agent-source = agent.soar
	spawn-debugger = false


#### SoarAgent Methods

`add_connector(AgentConnector)`
Adds the given connector and will invoke callbacks on it (such as on_input_phase)

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

`restart()`
Completely destroys the agent and creates + sources a new one

`kill()` 
Will stop the agent destroy the agent/kernel
	

## LanguageConnector
Defines a connector for putting NL messages on the agent's input-link and receiving messages from the agent
Used mostly for the Rosie Project. 

`send_message(message:str)` 
Sends the given message (which should be a single English sentence) to the agent
Replaces the previous message, if there is one

`register_message_callback(agent_message_callback)` 
The given callback function is called when the agent puts a message on the output-link






