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

## WMInterface:
An interface class which defines a standard way of adding/removing structures from working memory:

`is_added()`
Returns True if the structure is currently added to working memory

`add_to_wm(parent_id)`
Adds the structure to working memory under the given identifier

`update_wm(parent_id=None)`
Applies any changes to working memory
Note, if a `parent_id` is given and the item is not yet added to wm, it will add it

`remove_from_wm()`
Removes the structure from working memory

## SoarWME:
A class which can represent a WMElement with an `(<id> ^att value)` but takes care of actually interfacing with working memory

You can update its value whenever you want, it will not affect working memory. To change working memory, call `add_to_wm`, `update_wm`, and `remove_from_wm` during an event callback (like BEFORE_INPUT_PHASE)

## SoarUtils:

`SoarUtils.update_wm_from_tree(root_id, root_name, input_dict, wme_table)`

Will update working memory using the given `input_dict` as the provided structure rooted at `root_id`. 
Created wme's are stored in the given `wme_table`, which should be a dictionary that is kept across
multiple calls to this function. `root_name` specifies a prefix for each wme name in the wme_table. 

```
# input_dict should have the following structure:
{
  'attr1': getter() <- The value will be the result of calling the given getter function
  'attr2': dict   <- The value will be a child identifier with its own recursive substructure
}
```




`SoarUtils.extract_wm_graph(root_id, max_depth)`

Recursively explores all working memory reachable from the given root_id (up to max_depth),
builds up a graph structure representing all that information. 

Note: max_depth is optional, and the function is smart about handling loops (will not recurse forever)

```
# Returns a dictionary representing all wmes rooted at the given identifier:
{
  '__id__': Identifier - the root identifier of this node
  '__sym__': str - the symbol of root identifier of this node
  'attr1': str | float | int - a constant wme
  'attr2': dict - an identifier wme (recursive substructure)
  'attr3': list[values] - a list of values/dicts if attr3 is a multivalued attribute
}
```

`SoarUtils.print_wm_graph(wm_graph)`

Will print the graph produced by extract_wm_graph in a nicely formatted way


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

## TimeInfo
Adds timing information to the input-link, used internally by SoarAgent
	

## LanguageConnector
Defines a connector for putting NL messages on the agent's input-link and receiving messages from the agent
Used mostly for the Rosie Project. 

`send_message(message:str)` 
Sends the given message (which should be a single English sentence) to the agent
Replaces the previous message, if there is one

`register_message_callback(agent_message_callback)` 
The given callback function is called when the agent puts a message on the output-link
 

## RosieMessageParser
Provides static utility functions for parsing Rosie messages from the agent

`parse_message(msg_id:Identifier, msg_type:str)`
Takes the given identifier, representing a message from the Rosie agent of the given type, 
and turns it into a natural language string

`parse_obj(obj_id:Identifier)`
Turns the given identifier, representing a rosie world object, and
returns a natural language description of the object






