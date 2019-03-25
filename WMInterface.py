"""
This module defines a utility interface called WMInterface
which defines a standard interface for adding and removing things from working memory
"""

class WMInterface(object):
    """ An interface standardizing how to add/remove items from working memory """

    def __init__(self):
        self.added = False

    def is_added(self):
        """ Returns true if the wme is currently in soar's working memory """
        return self.added

    def add_to_wm(self, parent_id):
        """ Creates a structure in working memory rooted at the given parent_id """
        if self.added:
            self._remove_from_wm_impl()
        self._add_to_wm_impl(parent_id)
        self.added = True

    def update_wm(self):
        """ Updates the structure in Soar's working memory """
        if not self.added:
            return
        self._update_wm_impl()

    def remove_from_wm(self):
        """ Removes the structure from Soar's working memory """
        if not self.added:
            return
        self._remove_from_wm_impl()
        self.added = False


    ### Internal Methods - To be implemented by derived classes
    
    def _add_to_wm_impl(self, parent_id):
        """ Method to implement in derived class - add to working memory """
        pass

    def _update_wm_impl(self):
        """ Method to implement in derived class - update working memory """
        pass

    def _remove_from_wm_impl(self):
        """ Method to implement in derived class - remove from working memory """
        pass

