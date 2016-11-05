#!/usr/bin/env python3

"""
Resizes JPEG pictures to fit on a HDTV (1920x1080). Requires ImageMagick, Wand and libmagic.

TODO: Support any picture type: JPEG, PNG etc.
TODO: Specify TV size: HD, UHD
TODO: Specify diagonal size in inches -> calculate DPI
TODO: Flag for force delete existing pictures in out directory

Created on Jun 21, 2016

@author: Florin Rosca
"""

import re, math, collections, sys, getopt, os, magic
from wand.image import Image

Size = collections.namedtuple("Size", "width height")

SIZE = Size(1920, 1080)
RESOLUTION = Size(48, 48)
SCRIPT = os.path.basename(__file__)


class ValidationException(Exception):
    """ An exception thrown when a validation error occurs """
    def __init__(self,*args,**kwargs):
        Exception.__init__(self,*args,**kwargs)
       
        

def main(argv):
    """ Main method """
    inputdir = ""
    outputdir = ""
    try:
        if len(argv) == 0:
            raise getopt.GetoptError("Must have at least one argument")    
        opts, _ = getopt.getopt(argv, "hi:o:", ["help", "in=", "out="])
        for opt, arg in opts:
            if opt in ("-h", "--help"):
                raise getopt.GetoptError("Help") 
            elif opt in ("-i", "--in"):
                inputdir = arg
            elif opt in ("-o", "--out"):
                outputdir = arg
        resize4hdtv(inputdir, outputdir)
    except getopt.GetoptError:
        print("USAGE: {0} <options>".format(SCRIPT))
        print()
        print("OPTIONS:")
        print("   -i <directory>        The input directory")
        print("   -o <directory>        The output directory")
        print("   -h                    Show help")
        print("   --in=<directory>      The input directory")
        print("   --out=<directory>     The output directory")
        print("   --help                Show help")
        sys.exit(1)
    except ValidationException as ex:
        print("ERROR: {1}".format("".join(ex.args)))
        sys.exit(2)

        
def _validate(input_dir, output_dir):
    """ Validates input and output directories """
    
    if len(input_dir) == 0 or len(output_dir) == 0:
        raise ValidationException("Must specify an input and an output.") 
    if os.path.realpath(input_dir) == os.path.realpath(output_dir):
        raise ValidationException("The input must be different from the output.")
    if not os.path.exists(input_dir):
        raise ValidationException("'{0}' does not exist.".format(input_dir))
    

def _accept(dir_, file):
    """ Returns True if the file should be processed, False if not. """
    if file.startswith("."):
        return False
    return True


def resize4hdtv(input_dir, output_dir):
    """ Walks input directory, creates output directory if needed """
    print("Resizing...")
    _validate(input_dir, output_dir)
    # Counters for dirs, files and resized pictures
    count = { "dirs": 0, "files": 0, "resized": 0 }
    
    for src_dir, _, files in os.walk(input_dir):
        count["dirs"] += 1
        rel = os.path.relpath(src_dir, input_dir)
        dst_dir = os.path.join(output_dir, rel)
        if not os.path.exists(dst_dir):
            print("{0} does not exist, creating...".format(dst_dir))
            os.makedirs(dst_dir)
        for f in files:
            if not _accept(src_dir, f):
                continue
            src_path = os.path.join(src_dir, f)
            dst_path = os.path.join(dst_dir, f)
            count["files"] += 1
            if _resize(src_path, dst_path):
                count["resized"] += 1
               
    print("{0} directories, {1} files, {2} pictures resized.".format(count["dirs"], count["files"], count["resized"])) 
    print("Done.")
    
    
def _resize(input_path, output_path):
    """ Resizes one image, saves as JPG """
    
    print("{0} - > {1}".format(input_path, output_path))
    if os.path.exists(output_path):
        print("Already resized, skipping...")
        return False
    match = re.search("\(\d+\)\.jpg", input_path)
    if match:
        print("Duplicate, skipping...")
        return
        
    t = str(magic.from_file(input_path, mime=True))
    if t.find("image/jpeg") < 0:
        return False
    
    with Image(filename=input_path) as img:
        print("Old size    : {0}x{1}".format(img.width, img.height))
        img.resolution = RESOLUTION
        if img.width >= img.height:
            print("Orientation : Horizontal")
            s = SIZE.width / img.width
            size = Size(int(img.width * s), int(img.height * s))   
            img.resize(size.width, size.height)
            # Determine the height of a band to cut from the top and from the bottom of the picture
            y_crop = 0
            if size.height > SIZE.height:
                y_crop = int(math.ceil((size.height - SIZE.height) / 2))
                print("Crop        : 2*{0}".format(y_crop))  
                img.crop(0, y_crop, img.width, img.height - y_crop)
                            
        else:
            print("Orientation : Vertical")
            print("Crop        : None")
            s = SIZE.height / img.height
            size = Size(int(img.width * s), int(img.height * s))
            img.resize(size.width, size.height)
               
        print("New size    : {0}x{1}".format(img.width, img.height)) 
        img.format = "jpeg"
        # Sharpen the image. Parameters found somewhere here:
        # http://www.imagemagick.org/Usage/blur/#sharpen
        img.unsharp_mask(radius=2, sigma=1, amount=0.8, threshold=0.016)
        img.save(filename=output_path)
     
    return True


if __name__ == "__main__":
    main(sys.argv[1:])