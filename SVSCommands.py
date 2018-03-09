
class SVSCommands:
	# pos = [ x, y, z ] (list of 3 numbers)
    @staticmethod
    def pos_to_str(pos):
    	return "{:f} {:f} {:f}".format(pos[0], pos[1], pos[2])
    
	# rot = [ x, y, z ] (list of 3 numbers)
    @staticmethod
    def rot_to_str(rot):
    	return "{:f} {:f} {:f}".format(rot[0], rot[1], rot[2])
    
	# scl = [ x, y, z ] (list of 3 numbers)
    @staticmethod
    def scl_to_str(scl):
    	return "{:f} {:f} {:f}".format(scl[0], scl[1], scl[2])
	
    # Creates a set of 8 vertices forming a bounding box
    #   of unit size centered at the origin
    @staticmethod
    def bbox_verts():
    	return "0.5 0.5 0.5 0.5 0.5 -0.5 0.5 -0.5 0.5 0.5 -0.5 -0.5 -0.5 0.5 0.5 -0.5 0.5 -0.5 -0.5 -0.5 0.5 -0.5 -0.5 -0.5"
    
    @staticmethod
    def add_box(obj_id, pos=None, rot=None, scl=None):
        cmd = "add {:s} world v {:s}".format(obj_id, SVSCommands.bbox_verts())
        if pos: cmd += " p {:s}".format(SVSCommands.pos_to_str(pos))
        if rot: cmd += " r {:s}".format(SVSCommands.rot_to_str(rot))
        if scl: cmd += " s {:s}".format(SVSCommands.scl_to_str(scl))
        return cmd
    
    @staticmethod
    def change_pos(obj_id, pos):
        return "change {:s} p {:s}".format(obj_id, SVSCommands.pos_to_str(pos))
    
    @staticmethod
    def change_rot(obj_id, rot):
        return "change {:s} r {:s}".format(obj_id, SVSCommands.rot_to_str(rot))
    
    @staticmethod
    def change_scl(obj_id, scl):
        return "change {:s} s {:s}".format(obj_id, SVSCommands.scl_to_str(scl))
    
    @staticmethod
    def delete(obj_id):
    	return "delete {:s}".format(obj_id)
    
    @staticmethod
    def add_tag(obj_id, tag_name, tag_value):
    	return "tag add {:s} {:s} {:s}".format(obj_id, tag_name, tag_value)
    
    @staticmethod
    def change_tag(obj_id, tag_name, tag_value):
    	return "tag change {:s} {:s} {:s}".format(obj_id, tag_name, tag_value)
    
    @staticmethod
    def delete_tag(obj_id, tag_name):
    	return "tag delete {:s} {:s}".format(obj_id, tag_name)
