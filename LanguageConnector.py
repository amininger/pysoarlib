""" Used in the Rosie project to send and receive messages from the agent

Adds English sentences as a linked list of words on input-link.language
Handles send-message commands on the output link
"""
import sys

from string import digits
from .WMInterface import WMInterface
from .AgentConnector import AgentConnector
from .SoarUtils import SoarUtils

class Message(WMInterface):
    """ Represents a single sentence that can be added to working memory as a linked list """
    def __init__(self, message, num):
        """ message:string - a single natural language sentence
            num:int - a number indicating the id of the message """
        WMInterface.__init__(self)
        self.message = message.strip()
        self.num = num

        self.message_id = None

    def _add_to_wm_impl(self, parent_id):
        self.message_id = parent_id.CreateIdWME("sentence")
        self.message_id.CreateIntWME("sentence-number", self.num)
        self.message_id.CreateStringWME("complete-sentence", self.message)
        self.message_id.CreateStringWME("spelling", "*")

        # Get the punctutation character, if exists, and remove it
        punct = '.'
        if self.message[-1] in ".!?":
            punct = self.message[-1]
            self.message = self.message[:-1]

        # If there is a quote in the sentence, adds it as a single unit (not broken into words)
        # (In place of the quote, puts a _XXX_ placeholder)
        self.message = self.message.replace('|', '"')
        quote = None
        begin_quote = self.message.find('"')
        end_quote = self.message.find('"', begin_quote+1)
        if begin_quote != -1 and end_quote != -1:
            quote = self.message[begin_quote+1:end_quote]
            self.message = self.message[:begin_quote] + "_XXX_" + self.message[end_quote+1:]

        # Create a linked list of words with next pointers
        next_id = self.message_id.CreateIdWME("next")
        words = self.message.split()
        for word in words:
            if len(word) == 0:
                continue
            if word == "_XXX_":
                # Add the quote as a whole
                word = quote
                next_id.CreateStringWME("quoted", "true")
            next_id.CreateStringWME("spelling", word.lower())
            next_id = next_id.CreateIdWME("next")
        
        # Add punctuation at the end
        next_id.CreateStringWME("spelling", str(punct))
        next_id.CreateStringWME("next", "nil")

    def _remove_from_wm_impl(self):
        self.message_id.DestroyWME()
        self.message_id = None

class LanguageConnector(AgentConnector):
    """ Will handle natural language input and output to a soar agent
        For input - will add sentences onto the input link as a linked list
        For output - will take a message type and generate a natural language sentence """
    def __init__(self, agent, print_handler=None):
        AgentConnector.__init__(self, agent, print_handler)
        self.agent_message_callbacks = []
        self.add_output_command("send-message")

        self.current_message = None
        self.next_message_id = 1
        self.language_id = None

        self.messages_to_remove = set()

    def register_message_callback(self, agent_message_callback):
        self.agent_message_callbacks.append(agent_message_callback)

    def on_init_soar(self):
        if self.current_message != None:
            self.current_message.remove_from_wm()
            self.current_message = None
        if self.language_id != None:
            self.language_id.DestroyWME()
            self.language_id = None

    def send_message(self, message):
        if self.current_message != None:
            self.messages_to_remove.add(self.current_message)
        self.current_message = Message(message, self.next_message_id)
        self.next_message_id += 1

    def on_input_phase(self, input_link):
        if self.language_id == None:
            self.language_id = input_link.CreateIdWME("language")

        if self.current_message != None and not self.current_message.is_added():
            self.current_message.add_to_wm(self.language_id)

        for msg in self.messages_to_remove:
            msg.remove_from_wm()
        if len(self.messages_to_remove) > 0:
            self.messages_to_remove = set()

    def on_output_event(self, command_name, root_id):
        if command_name == "send-message":
            self.process_output_link_message(root_id)

    def process_output_link_message(self, root_id):
        message_type = root_id.FindByAttribute("type", 0).GetValueAsString()
        if not message_type:
            root_id.CreateStringWME("status", "error")
            root_id.CreateStringWME("error-info", "send-message has no type")
            self.print_handler("LanguageConnector: Error - send-message has no type")
            return

        message = self.translate_agent_message(root_id, message_type)
        for callback in self.agent_message_callbacks:
            callback(message)
        root_id.CreateStringWME("status", "complete")

    def translate_agent_message(self, root_id, message_type):
        msg_graph = SoarUtils.extract_wm_graph(root_id)
        message_parser = LanguageConnector.message_parser_map.get(message_type)
        if message_parser is not None and callable(message_parser):
            return message_parser(msg_graph)
        return message_type

    message_parser_map = {
        "ok": lambda msg_graph: "Ok",
        "unable-to-satisfy": lambda msg_graph: "I couldn't do that",
        "unable-to-interpret-message": lambda msg_graph: "I don't understand.",
        "missing-object": lambda msg_graph: "I lost the object I was using. Can you help me find it?",
        "index-object-failure": lambda msg_graph: "I couldn't find the referenced object",
        "no-proposed-action": lambda msg_graph: "I couldn't do that",
        "missing-argument": lambda msg_graph: "I need more information to do that action",
        "learn-location-failure": lambda msg_graph: "I don't know where I am.",
        "get-next-goal": lambda msg_graph: "What is the next goal or subtask?",
        "no-action-context-for-goal": lambda msg_graph: "I don't know what action that goal is for",
        "get-next-task": lambda msg_graph: "I'm ready for a new task",
        "get-next-subaction": lambda msg_graph: "What do I do next?",
        "confirm-pick-up": lambda msg_graph: "I have picked up the object.",
        "confirm-put-down": lambda msg_graph: "I have put down the object.",
        "stop-leading": lambda msg_graph: "You can stop following me",
        "retrospective-learning-failure": lambda msg_graph: "I was unable to learn the task policy",
        "report-successful-training": lambda msg_graph: "Ok",
        
        #added for games and puzzles
        "your-turn": lambda msg_graph: "Your turn.",
        "i-win": lambda msg_graph: "I win!",
        "i-lose": lambda msg_graph: "I lose.",
        "easy": lambda msg_graph: "That was easy!",
        "describe-game": lambda msg_graph: "Please setup the game.",
        "describe-puzzle": lambda msg_graph: "Please setup the puzzle.",
        "setup-goal": lambda msg_graph: "Please setup the goal state.",
        "tell-me-go": lambda msg_graph: "Ok: tell me when to go.",
        "setup-failure": lambda msg_graph: "Please setup the failure condition.",
        "define-actions": lambda msg_graph: "Can you describe the legal actions?",
        "describe-action": lambda msg_graph: "What are the conditions of the action.",
        "describe-goal": lambda msg_graph: "Please describe or demonstrate the goal.",
        "describe-failure": lambda msg_graph: "Please describe the failure condition.",
        "learned-goal": lambda msg_graph: "I have learned the goal.",
        "learned-action": lambda msg_graph: "I have learned the action.",
        "learned-failure": lambda msg_graph: "I have learned the failure condition.",
        "learned-heuristic": lambda msg_graph: "I have learned the heuristic.",
        "already-learned-goal": lambda msg_graph: "I know that goal and can recognize it.",
        "already-learned-action": lambda msg_graph: "I know that action and can recognize it.",
        "already-learned-failure": lambda msg_graph: "I know that failure condition and can recognize it.",
        "gotit": lambda msg_graph: "I've found a solution.",

        "single-word-message": lambda msg_graph: msg_graph['fields']['word'],
        "say-sentence": lambda msg_graph: msg_graph['fields']['sentence'],
        "cant-find-object": lambda msg_graph: "I can't find a " + msg_graph['fields']['object']['root-category'] + ", can you help?"


    }




