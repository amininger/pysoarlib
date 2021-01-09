# PySoarLib
## Aaron Mininger
### 2018

This is a python library module with code to help make working with Soar SML in python 
just a little bit easier. 

Methods do have docstrings, to read help information open a python shell and type
```
import pysoarlib
help(pysoarlib)
help(pysoarlib.SoarAgent)
```

* [SoarAgent](#soaragent)
* [Config Settings](#configsettings)
* [AgentConnector](#agentconnector)
* [IdentifierExtensions](#idextensions)
* [WMInterface](#wminterface)
* [SoarWME](#soarwme)
* [SVSCommands](#svscommands)
* [TimeConnector](#timeconnector)
* [util](#util)

<a name="soaragent"></a>
# SoarAgent
Defines a class used for creating a soar agent, sending commands, running it, etc.
There are a number of settings that you can use to configure the agent (see following subsection) and
can specify either by including them in the config file or by giving as keyword arguments
in the constructor. 

`SoarAgent(config_filename=None, print_handler=None, **kwargs)`     
Will create the soar kernel and agent, as well as source the agent files. 
`print_handler` specifies how output is handled (defaults to python print) and 
`config_filename` names a file with agent settings in it


`add_connector(AgentConnector, name:str)`    
Adds the given connector and will invoke callbacks on it (such as on_input_phase)

`get_connector(name:str)`    
Returns a connector of the given name, or None

`has_connector(name:str) -> Boolean`    
Returns true if the given connector exists

`add_print_event_handler(handler)`   
Will call the given handler during each soar print event (handler should be a method taking 1 string)

`connect()`     
Will register callbacks (call before running)

`disconnect()`     
Will deregister callbacks

`start()`     
Will cause the agent to start running in new thread (non-blocking)

`stop()`     
Will stop the agent

`execute_command(cmd:str, print_res:bool=False)`     
Sends the given command to the agent and returns the result as a string. If print_res=True it also prints the output using print_handler

`restart()`    
Completely destroys the agent and creates + sources a new one

`kill()`     
Will stop the agent destroy the agent/kernel


## Config Settings (kwargs or config file)
<a name="configsettings"></a>

These can be passed as keyword arguments to the SoarAgent constructor, 
or you can create a config file that contains these settings. 

| Argument           | Type     | Default    | Description                              |
| ------------------ | -------- | ---------- | ---------------------------------------- |
| `agent_name`       | str      | soaragent  | The soar agent's name |
| `agent_source`     | filename |            | The root soar file to source the agent productions  |
| `smem_source`      | filename |            | The root soar file that sources smem add commands |
| `source_output`    | enum str | summary    | How much detail to print when sourcing files: none, summary, or full |
| `watch_level`      | int      | 1          | Sets the soar watch/trace level, how much to print each DC (0=none) |
| `spawn_debugger`   | bool     | false      | If true, spawns the soar java debugger |
| `start_running`    | bool     | false      | If true, will automatically start running the agent |
| `write_to_stdout`  | bool     | false      | If true, will print all soar output to the print_handler |
| `print_handler`    | method   | print      | A method taking 1 string arg, handles agent output |
| `enable_log`       | bool     | false      | If true, writes all soar/agent output to a file |
| `log_filename`     | filename | agent-log.txt | The name of the log file to create |
| **time settings** <a name="timesettings"></a> |          |            |               |
| `use_time_connector`| bool    | false      | If true, creates a TimeConnector to put time info on the input-link |
| `clock_include_ms` | bool     | true       | Will include milliseconds for elapsed and clock times |
| `sim_clock`        | bool     | false      | If false, the clock shows real time. If true, it advances a fixed amount each DC |
| `clock_step_ms`    | int      | 50         | The number of milliseconds the simulated clock advances each decision cycle |

Instead of passing as arguments, you can include them in a file specified by config_filename
Each line in the file should be 'setting = value'

Example File:    
```
agent_name = Rosie    
agent_source = agent.soar    
spawn_debugger = false    
```


<a name="agentconnector"></a>
# AgentConnector
Defines an abstract base class for creating classes that connect to Soar's input/output links

`AgentConnector(agent:SoarAgent, print_handler:None)`     
print_handler determines how output is printed, defaults to normal python print

`add_output_command(command_name:str)`     
Will register a handler that listens to output link commands with the given name

`add_print_event_handler(handler:func)`     
Will register a print event handler (function taking 1 string argument) that will be called whenever a soar print event occurs. 

`on_init_soar()`     
Event Handler called when init-soar happens (need to release SML working memory objects)

`on_input_phase(input_link:Identifier)`     
Event Handler called every input phase

`on_output_event(command_name, root_id)`     
Event Handler called when a new output link command is created `(<output-link> ^command_name <root_id>)`





<a name="idextensions"></a>
# IdentifierExtensions 
These add a few helper methods to the sml.Identifier class:
(Do not need to import directly, come with any import from module)

`Identifier.GetChildString(attribute:str)`     
Given an attribute, will look for a child WME of the form `(<id> ^attribute <value>)` and return the value as a string

`Identifier.GetChildInt(attribute:str)`     
Given an attribute, will look for a child IntegerWME of the form `(<id> ^attribute <value>)` and return the value as an integer

`Identifier.GetChildFloat(attribute:str)`     
Given an attribute, will look for a child FloatWME of the form `(<id> ^attribute <value>)` and return the value as an float

`Identifier.GetChildId(attribute:str)`     
Given an attribute, will look for a child WME of the form `(<id> ^attribute <child_id>)` and return an Identifier with child_id as the root

`Identifier.GetAllChildIds(attribute:str=None)`     
Given an attribute, returns a list of Identifiers from all child WME's matching `(<id> ^attribute <child_id>)`
If no attribute is specified, all child Identifiers are returned

`Identifier.GetAllChildValues(attribute:str=None)`     
Given an attribute, returns a list of strings from all child WME's matching `(<id> ^attribute <value>)`
If no attribute is specified, all child WME values (non-identifiers) are returned

`Identifier.GetAllChildWmes()`     
Returns a list of (attr, val) tuples representing all wmes rooted at this identifier.
val will either be an Identifier or a string, depending on its type """


<a name="wminterface"></a>
# WMInterface:    
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


<a name="soarwme"></a>
# SoarWME:    
A class which can represent a WMElement with an `(<id> ^att value)` but takes care of actually interfacing with working memory

You can update its value whenever you want, it will not affect working memory. To change working memory, call `add_to_wm`, `update_wm`, and `remove_from_wm` during an event callback (like BEFORE_INPUT_PHASE)


<a name="svscommands"></a>
# SVSCommands:
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

<a name="timeconnector"></a>
# TimeConnector
An AgentConnector that will create time info on the input-link. 
Includes elapsed time since the agent started, and can have a real-time or simulated wall clock. 
It is enabled through the agent setting `use-time-connector=True`
There are several settings that control its behavior as described in [Config Settings](#timesettings). 


```
# Will add and update the following on the input-link:
([il] ^time [t])
([t] ^seconds [secs] # real-time seconds elapsed since start of agent
     ^milliseconds [ms] # real-time milliseconds elapsed since start
     ^steps [steps] # number of decision cycles since start of agent
     ^clock [clock])
([clock] ^hour [hr] # 0-23
         ^minute [min] # 0-59
         ^second [sec] # 0-59
         ^millisecond [ms] # 0-999
         ^epoch [sec] # Unix epoch time in seconds)
```

Also, if using a simulated clock, the agent can change the time itself using an output command:
```
([out] ^set-time [cmd])
([cmd] ^hour 9
       ^minute 15
       ^second 30) # optional 
```

<a name="util"></a>
# pysoarlib.util
Package containing several utility functions for reading/writing working memory through sml structures.

#### `parse_wm_printout(text:str)`   

Given a printout of soar's working memory (p S1 -d 4), parses it into a dictionary of wmes, 
where the keys are identifiers, and the values are lists of wme triples rooted at that id.

You can wrap the result with a PrintoutIdentifier(wmes, root_id) which will provide an Identifier-like
iterface for crawling over the graph structure. It provides all the methods in the IdentifierExtensions interface.


#### `extract_wm_graph(root_id, max_depth)`

Recursively explores all working memory reachable from the given root_id (up to max_depth),
builds up a graph structure representing all that information. 

Note: max_depth is optional (defaults to no depth limit), and the function is smart about handling cycles (will not recurse forever)

```
# Returns a WMNode object wrapping the root_id and containing links to children
node.id = root_id (Identifier)
node.symbol = string (The root_id symbol e.g. O34)
node.attributes() - returns a list of child attribute strings
node['attr'] = WMNode   # for child identifiers
node['attr'] = constant # for string, double, or int value
node['attr'] = [ val1, val2, ... ] # for multi-valued attributes 
               (values can be constants or WMNodes)
str(node) - will pretty-print the node and all children recursively
```


#### `update_wm_from_tree(root_id, root_name, input_dict, wme_table)`

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

#### `remove_tree_from_wm(wme_table)`    
      
Given a wme_table filled by `SoarUtils.update_wm_from_tree`, removes all wmes from working memory 



