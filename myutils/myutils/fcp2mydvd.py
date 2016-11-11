#!/usr/bin/env python3

"""
Converts Final Cut Pro chapter markers to Toast MyDVD.

Created on Nov 4, 2016

@author: Florin Rosca
"""

import sys, os, re, getopt, math, xml.dom
from xml.dom.minidom import parse
from fractions import Fraction


SCRIPT = os.path.basename(__file__)
verbose = False

class FractionalTime(object):
    numerator = 0
    denominator = 1
    
    def __init__(self, numerator, denominator):
        self.numerator = numerator
        self.denominator = denominator
        
    @classmethod
    def from_fcp_time(cls, s):
        numerator = 0
        denominator = 1
        m = re.match("(\d+)/?(\d+)?s", s)
        str_num = m.group(1)
        if str_num:
            numerator = int(str_num)
        str_den = m.group(2)
        if str_den:
            denominator = int(str_den)
        return cls(numerator, denominator)
    
    def __str__(self):
        return "{0}/{1}s".format(self.numerator, self.denominator)
    

class SmpteTime:
    hours = 0
    minutes = 0
    seconds = 0
    frames = 0
    
    def __init__(self, hours, minutes, seconds, frames):
        self.hours = hours
        self.minutes = minutes
        self.seconds = seconds
        self.frames = frames
    
    @classmethod
    def from_fractional_time(cls, ft, fps):
        total_time = ft.numerator / ft.denominator
        total_seconds = int(total_time)
        # FIXME: we are not taking into consideration drop frames. The rounding here introduces some errors: frames are off by one or two.
        frames = int(round((total_time - total_seconds) * fps))
        seconds = total_seconds % 60
        total_minutes = int(total_seconds / 60)
        minutes = total_minutes % 60
        hours = int(total_minutes / 60)
        return cls(hours, minutes, seconds, frames)
        
    def __str__(self):
        return "{0:02d}:{1:02d}:{2:02d}.{3:02d}".format(self.hours, self.minutes, self.seconds. self.frames)
  
        
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
                        _fcp_chapters(elem_project)
                        break
                break
    
    if not event_found:
        raise ParseException("Cannot find event {0}".format(input_event))
    if not project_found:
        raise ParseException("Cannot find project {0}".format(input_project))
   
    
def _fcp_chapters(elem_project):
    """ Extracts the chapter markers from the FCP project.
    
    Argument:
    elem_project -- a DOM element for the <project> node in the current FCP XML
    
    Returns a tuple (time_codes, time_base, time_code_format), where:
    * time_codes is an array of chapter fractional time tuples (time, base)
    * time_base is the denominator used for fractional times in the current FCP XML sequence, for example 30000
    * time_code_format is a string [DF|NDF] indicating drop frame (NTSC, 29.97fps when time_base is 30000) or no drop frame (30fps when time_base is 30000)
    """
    # Find sequence/spine/[clip asset-clip]
    # TODO: calculate MyDVD time code for markers
    sequence_count = 0
    for elem_sequence in elem_project.getElementsByTagName("sequence"):
        sequence_count += 1
        if sequence_count > 1:
            raise ParseException("More than one sequence")
        
        sequence_tc_format = _xml_attr(elem_sequence, "tcFormat", "NDF")
        ft_sequence_duration = _xml_attr_fcp_time(elem_sequence, "duration")
        time_base = ft_sequence_duration[1]
        
        # Determine target frames per second rate. We support only 29.97 and 30 fps
        # TODO: better way of determining target frame rate. Where is that in FCP XML?
        fps = 0
        if time_base == 30000:
            if sequence_tc_format == "DF":
                fps = 30000 / 1001
            if sequence_tc_format == "NDF":
                fps = 30000 / 1000
        else:
            raise ParseException("Time base not supported yet: {0}".format(time_base))
        
        if verbose:
            print()
            print("Sequence duration         : {0}".format(_fr2str(ft_sequence_duration, fps)))
            print("Sequence time code format : {0}".format(sequence_tc_format))
            print("Frame rate                : {0}".format(fps))
            print()
            # TODO: verify that ft_sequence_duration[1] is the base, 30000 = 29.97fps(?)
            
        chapters = []
        
        for elem_spine in elem_sequence.getElementsByTagName("spine"):
            for c1 in elem_spine.childNodes:
                if not c1.nodeType == xml.dom.Node.ELEMENT_NODE:
                    continue
                # This should be either a clip or a asset-clip node
                if not c1.tagName in ["clip", "asset-clip"]:
                    continue
                    
                elem_clip = c1
                # The offset relative to the parent sequence (beginning)
                t_clip_offset = _xml_attr_fcp_time(elem_clip, "offset")
                # The duration of the clip
                t_clip_duration = _xml_attr_fcp_time(elem_clip, "duration")
                # The start relative to the clip
                t_clip_start = _xml_attr_fcp_time(elem_clip, "start")

                # elem_clip.tagName is either clip or asset-clip here
                if verbose:
                    print("Start: {0:} Offset: {1} Duration: {2} Name: {3}".format(
                        _fr2str(t_clip_start, fps),
                        _fr2str(t_clip_offset, fps), 
                        _fr2str(t_clip_duration, fps), 
                        elem_clip.attributes["name"].value))
                        
                for c2 in elem_clip.childNodes:
                    if not c2.nodeType == xml.dom.Node.ELEMENT_NODE:
                        continue
                    # This should be either a clip or a asset-clip node
                    if not c2.tagName in ["chapter-marker"]:
                        continue 
                    elem_chapter_marker = c2  
                    t_chapter_marker_start = _xml_attr_fcp_time(elem_chapter_marker, "start")
                    # t_chapter_marker_duration = _xml_attr_fcp_time(elem_chapter_marker, "duration")
                    
                    # Use numbers.Fraction
                    f_clip_offset = Fraction(t_clip_offset[0], t_clip_offset[1])
                    f_clip_start = Fraction(t_clip_start[0], t_clip_start[1])
                    f_chapter_marker_start = Fraction(t_chapter_marker_start[0], t_chapter_marker_start[1])
                    
                    f_chapter_abs = f_clip_offset - f_clip_start + f_chapter_marker_start

                    # Fraction; numerator / denominator
                    chapter = (int(f_chapter_abs.numerator * time_base / f_chapter_abs.denominator), time_base)
                    chapters.append(chapter)
                    
        if verbose:
            print()
            for chapter in chapters:
                print("Chapter: {0}".format(_fr2str(chapter, fps)))
        
    return (chapters, time_base, sequence_tc_format)


def _fr2smpte(t, fps):
    """ Converts a fractional time tuple (time, base) to a SMPTE time tuple (h, m, s, f) using the specified frames per second rate """
    total_time = t[0] / t[1]
    total_seconds = int(total_time)
    # FIXME: we are not taking into consideration drop frames. The rounding here introduces some errors: frames are off by one or two.
    frames = int(round((total_time - total_seconds) * fps))
    seconds = total_seconds % 60
    total_minutes = int(total_seconds / 60)
    minutes = total_minutes % 60
    hours = int(total_minutes / 60)
    return (hours, minutes, seconds, frames)


def _fr2str(t, fps):
    """ Converts a fractional time tuple (time, base) to a SMPTE string hh:mm:ss.ff """
    return _smpte2str(_fr2smpte(t, fps))


def _smpte2str(t):
    """ Converts a SMPTE time tuple (h, m, s, f) to a SMPTE string hh:mm:ss.ff """
    # Unpacking the tuple, see http://stackoverflow.com/questions/15181927/new-style-formatting-with-tuple-as-argument
    return "{0:02d}:{1:02d}:{2:02d}.{3:02d}".format(*t)


def _xml_attr(elem, name, def_val):
    """ Reads the specified element attribute and returns its value or the specified value if the attribute cannot be found or it is empty """
    try:
        str_val = elem.attributes[name].value
        if not str_val:
            str_val = def_val
    except KeyError:
        return def_val
    return str_val
    
    
def _xml_attr_fcp_time(elem, attr):
    """ Reads the specified element attribute by name in the form ######/#####s and converts it to a tuple (time, base) representing a fraction """
    try:
        str_time = elem.attributes[attr].value
    except KeyError:
        str_time = "0s"
    m = re.match("(\d+)/?(\d+)?s", str_time)
    fr = [0, 1]
    str_num = m.group(1)
    if str_num:
        fr[0] = int(str_num)
    str_den = m.group(2)
    if str_den:
        fr[1] = int(str_den)
    return (fr[0], fr[1])
    
    
if __name__ == "__main__":
    main(sys.argv[1:])