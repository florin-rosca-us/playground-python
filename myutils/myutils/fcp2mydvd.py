#!/usr/bin/env python3

"""
Converts Final Cut Pro chapter markers to Toast MyDVD.

Created on Nov 4, 2016

@author: Florin Rosca
"""

import sys, os, getopt, xml.dom

from xml.dom.minidom import parse

SCRIPT = os.path.basename(__file__)
verbose = False


class ParseException(Exception):
    """ An exception throws when a validation error occurs """
    def __init__(self,*args,**kwargs):
        Exception.__init__(self,*args,**kwargs)
        
        
def main(argv):
    global verbose
    input_path = ""
    input_event = ""
    input_project = ""
    output_path = ""
    verbose = False
    try:
        if len(argv) == 0:
            raise getopt.GetoptError("Must have at least one argument")
        opts, _ = getopt.getopt(argv, "hi:e:p:o:v", ["help", "in=", "event=", "project=", "out=", "verbose"])
        
        for opt, arg in opts:
            if opt in ("-h", "--help"):
                raise getopt.GetoptError("Help") 
            elif opt in ("-i", "--in"):
                input_path = arg
            elif opt in ("-e", "--event"):
                input_event = arg
            elif opt in ("-p", "--project"):
                input_project = arg
            elif opt in ("-o", "--out"):
                output_path = arg
            elif opt in ("-v", "--verbose"):
                verbose = True
            
        if not input_path:
            raise getopt.GetoptError("Missing input XML file")
        if not input_event:
            raise getopt.GetoptError("Missing event name")
        if not input_project:
            raise getopt.GetoptError("Missing project name")
        if not output_path:
            raise getopt.GetoptError("Missing output XML file")
        
        fcp2mydvd(input_path, input_event, input_project, output_path)
        
    except getopt.GetoptError:
        print("USAGE: {0} <options>".format(SCRIPT))
        print("")
        print("OPTIONS:")
        print("   -i <file>           The input Final Cut Pro XML file")
        print("   -e <NAME>           The event name in the Final Cut Pro library")
        print("   -p <NAME>           The project name under the event in the Final Cut Pro library")
        print("   -o <file>           The output Toast MyDVD file")
        print("   -h                  Show help")
        print("   -v                  Show details")
        print("   --in=<file>         The input Final Cut Pro XML file")
        print("   --event=<NAME>      The event name in the Final Cut Pro library")
        print("   --project=<NAME>    The project name under the event in the Final Cut Pro library")
        print("   --out=<file>        The output Toast MyDVD file")
        print("   --help              Show help")
        print("   --verbose           Show details")
        sys.exit(1)
        
    except ParseException as ex:
        print("ERROR: {0}".format("".join(ex.args)))
        sys.exit(2)
        
        
def fcp2mydvd(input_path, input_event, input_project, output_path):
    """ Converts Final Cut Pro chapter markers to Toast MyDVD. """
    
    global verbose
    input_dom = parse(input_path)
    output_dom = parse(output_path)

    input_doc = input_dom.documentElement
    output_doc = output_dom.documentElement
    
    if input_doc.tagName != "fcpxml":
        raise ParseException("The input is not a Final Cut Pro XML file") 
    if output_doc.tagName != "MDProject":
        raise ParseException("The output is not a Toast MyDVD project file") 
    if not input_event:
        raise ParseException("Missing event name")
    if not input_project:
        raise ParseException("Missing project name")
    
    if verbose:
        print("Looking for {0}/{1}...".format(input_event, input_project))

    # Search for library/event/project matching the input parameters
    event_found = False
    project_found = False
    
    for elem_lib in input_doc.getElementsByTagName("library"):
        for elem_event in elem_lib.getElementsByTagName("event"):
            event_name = elem_event.attributes["name"].value
            if verbose:
                print("Event: {0}".format(event_name))
            if event_name == input_event:
                event_found = True
                for elem_project in elem_event.getElementsByTagName("project"):
                    project_name = elem_project.attributes["name"].value
                    if verbose:
                        print("Project: {0}".format(project_name))
                    if project_name == input_project:
                        project_found = True
                        _project(elem_project)
                        break
                break
    
    if not event_found:
        raise ParseException("Cannot find event {0}".format(input_event))
    if not project_found:
        raise ParseException("Cannot find project {0}".format(input_project))
   
    
def _project(elem_project):
    """ Extracts the chapter markers from the project """
    # Find sequence/spine/[clip asset-clip]
    # TODO: calculate MyDVD timecode for markers
    sequence_count = 0
    for elem_sequence in elem_project.getElementsByTagName("sequence"):
        sequence_count += 1
        if sequence_count > 1:
            raise ParseException("More than one sequence")
        for elem_spine in elem_sequence.getElementsByTagName("spine"):
            for child in elem_spine.childNodes:
                if child.nodeType == xml.dom.Node.ELEMENT_NODE:
                    # This should be either a clip or a asset-clip node
                    if verbose:
                        print("{0} name: {1}".format(child.tagName, child.attributes["name"].value))
                    
        
    return True
    
    
if __name__ == "__main__":
    main(sys.argv[1:])