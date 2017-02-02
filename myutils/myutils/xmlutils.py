#!/usr/bin/env python3

"""
Collection of XML DOM utilities.

Created on Feb 01, 2017

@author: Florin Rosca
"""

import xml.dom


class ParseException(Exception):
    """ An exception throws when a validation error occurs. """
    def __init__(self, *args, **kwargs):
        Exception.__init__(self, *args, **kwargs)
        
        
def get_attr(elem, name, def_val):
    """ Returns the attribute value or the default value if the attribute cannot be found or it is empty. """
    try:
        str_val = elem.attributes[name].value
        if not str_val:
            str_val = def_val
    except KeyError:
        return def_val
    return str_val


def get_child(parent, name):
    """ Returns the first child node that matches the specified tag name. """
    for child in parent.childNodes:
        if not child.nodeType == xml.dom.Node.ELEMENT_NODE:
            continue 
        if child.tagName == name:
            return child
    return None


def get_child_or_raise(parent, name, error):
    """ Returns the first child node that matches the specified tag name or raises a ParseException if a child node with the specified name cannot be found. """
    child = get_child(parent, name)
    if child is None:
        raise ParseException(error)
    return child


def get_child_with_attr(parent, tagName, attrName, value):
    """ Returns the first child node that matches the specified tag name and has an attribute with the specified name and value or None if a node cannot be found. """
    for elem in get_children_by_name(parent, tagName):
        if get_attr(elem, attrName, None) == value:
            return elem
    return None


def get_children_by_name(parent, name):
    """ Returns all child nodes that matches the specified tag name. """
    children = []
    for child in parent.childNodes:
        if not child.nodeType == xml.dom.Node.ELEMENT_NODE:
            continue
        if child.tagName == name:
            children.append(child)
    return children


def get_children_by_names(parent, names):
    """ Returns all child nodes that matches one of the specified tag names. """
    children = []
    for child in parent.childNodes:
        if not child.nodeType == xml.dom.Node.ELEMENT_NODE:
            continue
        if child.tagName in names:
            children.append(child)
    return children


def get_text(elem):
    """ Returns the text of the specified element. """
    for child in elem.childNodes:
        if child.nodeType == xml.dom.Node.TEXT_NODE:
            return child.data
    return ''
    
    
def remove_children(elem):
    """ Removes all children nodes of the specified element. """
    # Must copy the child nodes to a list first
    for child in list(elem.childNodes):
        elem.removeChild(child)     
