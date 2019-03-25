""" Used in the Rosie project to send and receive messages from the agent

Adds English sentences as a linked list of words on input-link.language
Handles send-message commands on the output link
"""
import sys

from string import digits
from .AgentConnector import AgentConnector

class Message:
    """ Represents a single sentence that can be added to working memory as a linked list """
    def __init__(self, message, num):
        """ message:string - a single natural language sentence
            num:int - a number indicating the id of the message """
        self.message = message.strip()
        self.num = num

        self.message_id = None
        self.added = False

    def is_added(self):
        return self.added

    def add_to_wm(self, parent_id):
        if self.added:
            self.remove_from_wm()

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
        self.added = True

    def update_wm(self):
        pass

    def remove_from_wm(self):
        if not self.added or self.message_id == None:
            return
        self.message_id.DestroyWME()
        self.message_id = None
        self.added = False

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
        message_type = root_id.GetChildString("type");
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
        message = LanguageConnector.simple_messages.get(message_type);
        if message:
            return message
        return message_type

    simple_messages = {
        "ok": "Ok",
        "unable-to-satisfy": "I couldn't do that",
        "unable-to-interpret-message": "I don't understand.",
        "missing-object": "I lost the object I was using. Can you help me find it?",
        "index-object-failure": "I couldn't find the referenced object",
        "no-proposed-action": "I couldn't do that",
        "missing-argument": "I need more information to do that action",
        "learn-location-failure": "I don't know where I am.",
        "get-goal-info": "What is the goal?",
        "no-action-context-for-goal": "I don't know what action that goal is for",
        "get-next-task": "I'm ready for a new task",
        "get-next-subaction": "What do I do next?",
        "confirm-pick-up": "I have picked up the object.",
        "confirm-put-down": "I have put down the object.",
        "stop-leading": "You can stop following me",
        "retrospective-learning-failure": "I was unable to learn the task policy",
        
        #added for games and puzzles
        "your-turn": "Your turn.",
        "i-win": "I win!",
        "i-lose": "I lose.",
        "easy": "That was easy!",
        "describe-game": "Please setup the game.",
        "describe-puzzle": "Please setup the puzzle.",
        "setup-goal": "Please setup the goal state.",
        "tell-me-go": "Ok: tell me when to go.",
        "setup-failure": "Please setup the failure condition.",
        "define-actions": "Can you describe the legal actions?",
        "describe-action": "What are the conditions of the action.",
        "describe-goal": "Please describe or demonstrate the goal.",
        "describe-failure": "Please describe the failure condition.",
        "learned-goal": "I have learned the goal.",
        "learned-action": "I have learned the action.",
        "learned-failure": "I have learned the failure condition.",
        "learned-heuristic": "I have learned the heuristic.",
        "already-learned-goal": "I know that goal and can recognize it.",
        "already-learned-action": "I know that action and can recognize it.",
        "already-learned-failure": "I know that failure condition and can recognize it.",
        "gotit": "I've found a solution."
    }




