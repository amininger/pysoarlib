""" Used in the Rosie project to parse messages from the Rosie Agent

    Handles send-message commands on the output link
"""
import sys

from string import digits
from .SoarUtils import SoarUtils

class RosieMessageParser:
    def parse_message(root_id, message_type):
        msg_graph = SoarUtils.extract_wm_graph(root_id)
        message_parser = RosieMessageParser.message_parser_map.get(message_type)
        if message_parser is not None and callable(message_parser):
            return message_parser(msg_graph)
        return message_type

    def parse_obj(obj_id):
        words = []
        preds_id = obj_id.GetChildId("predicates")
        words.append(preds_id.GetChildString("size"))
        words.append(preds_id.GetChildString("color"))
        words.append(preds_id.GetChildString("modifier1"))
        words.append(preds_id.GetChildString("shape"))

        name = preds_id.GetChildString("name")
        words.append(name if name is not None else obj_id.GetChildString("root-category"))
        obj_desc = " ".join(word for word in words if word is not None)
        return obj_desc.translate(str.maketrans('', '', digits))

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
        "cant-find-object": lambda msg_graph: "I can't find " + \
            RosieMessageParser.parse_obj(msg_graph['fields']['object']['__id__']) + \
            ", can you help?"
    }

