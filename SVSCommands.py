"""
This module defines a set of methods that generate SVS string commands 
"""
class SVSCommands:
    """ Contains static methods that generate SVS string commands

    These can then be passed to agent.SendSVSCommands
    Note that all transforms (pos, rot, scale) should be lists of 3 floats
    """
    @staticmethod
    def pos_to_str(pos):
        """ Returns a string of 3 space-separated position values """
        return "{:f} {:f} {:f}".format(pos[0], pos[1], pos[2])
    
    @staticmethod
    def rot_to_str(rot):
        """ Returns a string of 3 space-separated rotation values """
        return "{:f} {:f} {:f}".format(rot[0], rot[1], rot[2])
    
    @staticmethod
    def scl_to_str(scl):
        """ Returns a string of 3 space-separated scale values """
        return "{:f} {:f} {:f}".format(scl[0], scl[1], scl[2])
    
    @staticmethod
    def bbox_verts():
        """ Returns a string of 8 vertices (24 numbers) forming a bounding box

        It is of unit size centered at the origin
        """
        return "0.5 0.5 0.5 0.5 0.5 -0.5 0.5 -0.5 0.5 0.5 -0.5 -0.5 -0.5 0.5 0.5 -0.5 0.5 -0.5 -0.5 -0.5 0.5 -0.5 -0.5 -0.5"

    @staticmethod
    def add_node(node_id, pos=None, rot=None, scl=None, parent="world"):
        """ Returns an SVS command for adding a graph node to the scene (no geometry) """
        cmd = "add {:s} {:s} ".format(node_id, parent)
        if pos: cmd += " p {:s}".format(SVSCommands.pos_to_str(pos))
        if rot: cmd += " r {:s}".format(SVSCommands.rot_to_str(rot))
        if scl: cmd += " s {:s}".format(SVSCommands.scl_to_str(scl))
        return cmd
    
    @staticmethod
    def add_box(obj_id, pos=None, rot=None, scl=None, parent="world"):
        """ Returns an SVS command for adding a bounding box object to the scene """
        cmd = "add {:s} {:s} v {:s}".format(obj_id, parent, SVSCommands.bbox_verts())
        if pos: cmd += " p {:s}".format(SVSCommands.pos_to_str(pos))
        if rot: cmd += " r {:s}".format(SVSCommands.rot_to_str(rot))
        if scl: cmd += " s {:s}".format(SVSCommands.scl_to_str(scl))
        return cmd
    
    @staticmethod
    def change_pos(obj_id, pos):
        """ Returns an SVS command for changing the position of an svs object """
        return "change {:s} p {:s}".format(obj_id, SVSCommands.pos_to_str(pos))
    
    @staticmethod
    def change_rot(obj_id, rot):
        """ Returns an SVS command for changing the rotation of an svs object """
        return "change {:s} r {:s}".format(obj_id, SVSCommands.rot_to_str(rot))
    
    @staticmethod
    def change_scl(obj_id, scl):
        """ Returns an SVS command for changing the scale of an svs object """
        return "change {:s} s {:s}".format(obj_id, SVSCommands.scl_to_str(scl))
    
    @staticmethod
    def delete(obj_id):
        """ Returns an SVS command for deleting an object """
        return "delete {:s}".format(obj_id)
    
    @staticmethod
    def add_tag(obj_id, tag_name, tag_value):
        """ Returns an SVS command for adding a tag to an object (^name value) """
        return "tag add {:s} {:s} {:s}".format(obj_id, tag_name, tag_value)
    
    @staticmethod
    def change_tag(obj_id, tag_name, tag_value):
        """ Returns an SVS command for changing a tag on an object (^name value) """
        return "tag change {:s} {:s} {:s}".format(obj_id, tag_name, tag_value)
    
    @staticmethod
    def delete_tag(obj_id, tag_name):
        """ Returns an SVS command for deleting a tag with the given name from an object """
        return "tag delete {:s} {:s}".format(obj_id, tag_name)
