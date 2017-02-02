#!/usr/bin/env python3

"""
Converts Final Cut Pro chapter markers to Toast MyDVD.
Uses Python XML DOM, see https://docs.python.org/2/library/xml.dom.html

Created on Nov 4, 2016

@author: Florin Rosca
"""

from fractions import Fraction
import sys, os, re, getopt
from xml.dom.minidom import parse
import xmlutils
from xmlutils import ParseException

from pip._vendor.pyparsing import basestring


SCRIPT = os.path.basename(__file__)
_verbose = False

class FractionalTime(object):
    """ A time code as a fraction nnnnnn/ddddd. Example: 1001/30000.
    
    We are using this instead of a math.Fraction to preserve the denominator.
    The math.Fraction class reduces the fraction and in some cases loses the original denominator.
    """
    numerator = 0
    denominator = 1
    
    def __init__(self, numerator, denominator):
        """ Creates an instance.
        
        Arguments:
        * numerator -- must be zero or a positive integer
        * denominator -- must be a positive integer
        
        """
        assert isinstance(numerator, int) and numerator >= 0
        assert isinstance(denominator, int) and denominator > 0
        self.numerator = numerator
        self.denominator = denominator
        
    @classmethod
    def from_fcp_time(cls, s):
        """ Creates an instance from a Final Cut Pro time code string. Example: 1726725/30000s.
        """
        assert isinstance(s, str)
        numerator = 0
        denominator = 1
        m = re.match('(\d+)/?(\d+)?s', s)
        str_num = m.group(1)
        if str_num:
            numerator = int(str_num)
        str_den = m.group(2)
        if str_den:
            denominator = int(str_den)
        return cls(numerator, denominator)
    
    def __str__(self):
        """ Converts this instance to a string.
        """
        return '{0}/{1}s'.format(self.numerator, self.denominator)
    
    def to_fraction(self):
        return Fraction(self.numerator, self.denominator)
    
    def to_smpte(self, fps):
        assert fps > 0
        return SmpteTime.from_fractional_time(self, fps)
    

class SmpteTime(object):
    """ A SMPTE time code: hh:mm:ss.ff
    """
    hours = 0
    minutes = 0
    seconds = 0
    frames = 0
    # TODO: add fps, without that SMPTE is ambiguous
    
    def __init__(self, hours, minutes, seconds, frames):
        """ Creates an instance.
        """
        # We don't know how many frames per second so at least check if frames < 100
        assert isinstance(frames, int) and frames >= 0 and frames < 100
        assert isinstance(seconds, int) and seconds >= 0 and seconds < 60
        assert isinstance(minutes, int) and minutes >= 0 and minutes < 60
        assert isinstance(hours, int) and hours >= 0 and hours < 99
        self.hours = hours
        self.minutes = minutes
        self.seconds = seconds
        self.frames = frames
    
    @classmethod
    def from_fractional_time(cls, ft, fps):
        """ Creates an instance from a FractionalTime instance using the specified frame per seconds rate.
        """
        assert isinstance(ft, FractionalTime)
        assert fps > 0
        total_time = ft.numerator / ft.denominator
        total_seconds = int(total_time)
        # FIXME: we are not taking into consideration drop frames. The rounding here seems to introduce some errors: frames are off by one or two.
        frames = int(round((total_time - total_seconds) * fps))
        seconds = total_seconds % 60
        total_minutes = int(total_seconds / 60)
        minutes = total_minutes % 60
        hours = int(total_minutes / 60)
        return cls(hours, minutes, seconds, frames)
        
    def __str__(self):
        return '{0:02d}:{1:02d}:{2:02d}.{3:02d}'.format(self.hours, self.minutes, self.seconds, self.frames)
  

class FcpChapter(object):
    """ A chapter has an offset and a name.
    """
    offset = FractionalTime(0, 1)
    name = ""
    
    def __init__(self, offset, name):
        assert isinstance(offset, FractionalTime)
        assert name is not None
        self.offset = offset
        self.name = name


class FcpProject(object):
    """ A FCP project 
    """
    event = ""
    name = ""
    time_base = 1
    tc_format = 'DF'
    chapters = None
    
    def __init__(self, event, name, time_base, tc_format, chapters):
        assert isinstance(event, basestring)
        assert isinstance(name, basestring)
        assert isinstance(time_base, int)
        assert isinstance(tc_format, basestring)
        # TODO: assert chapters is an array of FcpChapter objects
        assert chapters != None
        self.event = event
        self.name = name
        self.time_base = time_base
        self.tc_format = tc_format
        self.chapters = chapters
    
    
def main(argv):
    global _verbose
    input_path = ""
    input_event = ""
    input_project = ""
    output_path = ""
    _verbose = False
    try:
        if len(argv) == 0:
            raise getopt.GetoptError('Must have at least one argument')
        opts, _ = getopt.getopt(argv, 'hi:e:p:o:v', ['help', 'in=', 'event=', 'project=', 'out=', '_verbose'])
        
        for opt, arg in opts:
            if opt in ('-h', '--help'):
                raise getopt.GetoptError('Help') 
            elif opt in ('-i', '--in'):
                input_path = arg
            elif opt in ('-e', '--event'):
                input_event = arg
            elif opt in ('-p', '--project'):
                input_project = arg
            elif opt in ('-o', '--out'):
                output_path = arg
            elif opt in ('-v', '--_verbose'):
                _verbose = True
            
        if not input_path:
            raise getopt.GetoptError('Missing input XML file')
        if not input_event:
            raise getopt.GetoptError('Missing event name')
        if not input_project:
            raise getopt.GetoptError('Missing project name')
        if not output_path:
            raise getopt.GetoptError('Missing output XML file')
        
        fcp2mydvd(input_path, input_event, input_project, output_path)
        
    except getopt.GetoptError:
        print('USAGE: {0} <options>'.format(SCRIPT))
        print('')
        print('OPTIONS:')
        print('   -i <file>           The input Final Cut Pro XML file')
        print('   -e <NAME>           The event name in the Final Cut Pro library')
        print('   -p <NAME>           The project name under the event in the Final Cut Pro library')
        print('   -o <file>           The output Toast MyDVD file')
        print('   -h                  Show help')
        print('   -v                  Show details')
        print('   --in=<file>         The input Final Cut Pro XML file')
        print('   --event=<NAME>      The event name in the Final Cut Pro library')
        print('   --project=<NAME>    The project name under the event in the Final Cut Pro library')
        print('   --out=<file>        The output Toast MyDVD file')
        print('   --help              Show help')
        print('   --_verbose           Show details')
        sys.exit(1)
        
    except ParseException as ex:
        print('ERROR: {0}'.format(''.join(ex.args)))
        sys.exit(2)
        
        
def fcp2mydvd(fcp_path, fcp_event, fcp_project, mydvd_path):
    """ Converts Final Cut Pro chapter markers to Toast MyDVD. """
    _set_mydvd_chapters(mydvd_path, _get_fcp_project(fcp_path, fcp_event, fcp_project))


def _get_fcp_project(path, event, project):
    """ Extracts FCP chapters.
        
    Arguments:
        * path -- the path to the input FCP XML file
        * event -- the event name
        * project -- the project name
    
    Returns:
        A FcpProject instance    
    """
    global _verbose
    if _verbose:
        print('Looking for {0}/{1}...'.format(event, project))
        print()

    dom = parse(path)
    doc = dom.documentElement
    if doc.tagName != 'fcpxml':
        raise ParseException('The input is not a Final Cut Pro XML file') 
    if not event:
        raise ParseException('Missing event name')
    if not project:
        raise ParseException('Missing project name')
            
    # for elem_lib in doc.getElementsByTagName('library'):
    elem_lib = xmlutils.get_child_or_raise(doc, 'library', 'Cannot find a library')
    elem_event = xmlutils.get_child_with_attr(elem_lib, 'event', 'name', event)   
    if elem_event is None:
        raise ParseException('Cannot find event {0}'.format(event))

    elem_project = xmlutils.get_child_with_attr(elem_event, 'project', 'name', project)    
    elem_sequence = xmlutils.get_child_or_raise(elem_project, 'sequence', 'Cannot find a sequence')    
    
    tc_format = xmlutils.get_attr(elem_sequence, 'tcFormat', 'NDF')
    seq_duration = FractionalTime.from_fcp_time(xmlutils.get_attr(elem_sequence, 'duration', '0s'))
    time_base = seq_duration.denominator
    # Guess the  target frames per second rate. We support only 29.97 and 30 fps
    # TODO: Better way of determining target frame rate. Where is that in FCP XML?
    fps = 0
    if time_base == 30000:
        if tc_format == 'DF':
            fps = 30000 / 1001
        if tc_format == 'NDF':
            fps = 30000 / 1000
    else:
        raise ParseException('Time base not supported yet: {0}'.format(time_base))
    if _verbose:
        print('Sequence duration         : {0}'.format(seq_duration.to_smpte(fps)))
        print('Sequence time code format : {0}'.format(tc_format))
        print('Frame rate                : {0}'.format(fps))
        print()
        # TODO: verify that seq_duration[1] is the base, 30000 = 29.97fps(?)
    
    chapters = _get_fcp_chapters(elem_sequence, time_base, fps)
    return FcpProject(event, project, time_base, tc_format, chapters)
    
    
def _get_fcp_chapters(elem_sequence, time_base, fps):
    global _verbose
    if _verbose:
        print('Looking for chapters...')
        print()
        
    chapters = []
    elem_spine = xmlutils.get_child_or_raise(elem_sequence, 'spine', 'Cannot find a spine element')
    for elem_clip in xmlutils.get_children_by_names(elem_spine, ['clip', 'asset-clip']):       
        ft_clip_offset = FractionalTime.from_fcp_time(xmlutils.get_attr(elem_clip, 'offset', '0s'))
        ft_clip_duration = FractionalTime.from_fcp_time(xmlutils.get_attr(elem_clip, 'duration', '0s'))
        ft_clip_start = FractionalTime.from_fcp_time(xmlutils.get_attr(elem_clip, 'start', '0s'))
        ft_tc_format = xmlutils.get_attr(elem_clip, 'tcFormat', 'DF')
        if _verbose:
            print('Clip Offset: {0:} Duration: {1} Start: {2} TimeCodeFormat: {3} Name: {4}'.format(
                ft_clip_offset.to_smpte(fps),
                ft_clip_duration.to_smpte(fps),
                ft_clip_start.to_smpte(fps),
                ft_tc_format.rjust(3),
                elem_clip.attributes['name'].value))
                
        for elem_chapter_marker in xmlutils.get_children_by_name(elem_clip, 'chapter-marker'):
            chapter_name = xmlutils.get_attr(elem_chapter_marker, 'value', '')            
            # Get chapter offset relative to the beginning of the sequence
            ft_chapter_marker_start = FractionalTime.from_fcp_time(xmlutils.get_attr(elem_chapter_marker, 'start', '0s'))
            # Convert FractionalTime to numbers.Fraction
            fr = ft_clip_offset.to_fraction() - ft_clip_start.to_fraction() + ft_chapter_marker_start.to_fraction()
            # Normalize fractional time: use time base
            chapter_offset = FractionalTime(int(fr.numerator * time_base / fr.denominator), time_base)
            # Append to array                    
            chapters.append(FcpChapter(chapter_offset, chapter_name))
               
    if _verbose:
        print()
         
    if _verbose:
        for chapter in chapters:
            print('Chapter: Offset: {0} Name: {1}'.format(chapter.offset.to_smpte(fps), chapter.name))
        print()

        
    return chapters


def _set_mydvd_chapters(path, fcp_project):
    """ Exports the specified chapters to the specified toast file """   
    global _verbose
    if _verbose:
        print('Saving...')
        print()
        
    if not fcp_project:
        raise ParseException('No project')    
    dom = parse(path)
    doc = dom.documentElement
    if doc.tagName != 'MDProject':
        raise ParseException('The output is not a Toast MyDVD project file') 

    elem_main_menu = xmlutils.get_child_or_raise(doc, 'MDMenu', 'Cannot find main menu')
    elem_main_menu_children = xmlutils.get_child_or_raise(elem_main_menu, 'children', 'Cannot find main menu children')
    
    # We are looking for the first title in the main menu. We do not support more than one title
    elem_title = xmlutils.get_child_or_raise(elem_main_menu_children, 'MDTitle', 'Cannot find a title')

    # We are using the thumbnail URL for creating chapter markers
    elem_preview_thumbnail = xmlutils.get_child_or_raise(elem_title, 'previewThumbnail', 'Cannot find preview thumbnail')
    elem_url = xmlutils.get_child_or_raise(elem_preview_thumbnail, 'url', 'Cannot find thumbnail URL')
    url = xmlutils.get_text(elem_url)
    if _verbose:
        print ('URL: {0}'.format(url))


    elem_title_children = xmlutils.get_child_or_raise(elem_title, 'children', 'Cannot find title children') 
    elem_title_menu = xmlutils.get_child_or_raise(elem_title_children, 'MDMenu', 'Cannot find title menu')
    elem_title_menu_children = xmlutils.get_child_or_raise(elem_title_menu, 'children', 'Cannot find title menu children')
    
    # Remove all children of MDMenu/children
    xmlutils.remove_children(elem_title_menu_children)
    
    # TODO: Add new chapters

    print(str(doc.toxml()))
    
    
if __name__ == "__main__":
    main(sys.argv[1:])
