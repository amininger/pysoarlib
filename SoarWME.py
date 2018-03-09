class SoarWME(object):
    def __init__(self, att, val):
        self.att = att
        self.val = val
        self.wme = None

        self.added = False
        self.changed = False

        if type(val) == int:
            self.create_wme = self.create_int_wme
        elif type(val) == float:
            self.create_wme = self.create_float_wme
        else:
            self.create_wme = self.create_string_wme

    def set_value(self, newval):
        if self.val != newval:
            self.val = newval
            self.changed = True

    def is_added(self):
        return self.added

    def create_int_wme(self, id, att, val):
        return id.CreateIntWME(att, val)

    def create_float_wme(self, id, att, val):
        return id.CreateFloatWME(att, val)

    def create_string_wme(self, id, att, val):
        return id.CreateStringWME(att, str(val))

    def add_to_wm(self, parent_id):
        if self.wme != None:
            self.remove_from_wm()
        self.wme = self.create_wme(parent_id, self.att, self.val)
        self.added = True

    def update_wm(self):
        if self.wme == None or not self.changed:
            return
        self.wme.Update(self.val)
        self.changed = False

    def remove_from_wm(self):
        if self.wme != None:
            self.wme.DestroyWME()
            self.wme = None
        self.added = False


