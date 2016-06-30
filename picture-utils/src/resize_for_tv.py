#!/opt/local/bin/python3

'''
Resizes pictures to fit on a HDTV (1920x1080). Requires ImageMagick, Wand and libmagic.

TODO: Specify TV size: HD, UHD
TODO: Specify diagonal size in inches -> calculate DPI
TODO: Flag for force delete existing pictures in out directory

Created on Jun 21, 2016

@author: Florin
'''
import re, math, collections, sys, getopt, os, magic
from wand.image import Image

Size = collections.namedtuple("Size", "width height")

SIZE = Size(1920, 1080)
RESOLUTION = Size(48, 48)
SCRIPT = os.path.basename(__file__)


class ValidationException(Exception):
    ''' An exception throws when a validation error occurs '''
    def __init__(self,*args,**kwargs):
        Exception.__init__(self,*args,**kwargs)
       
        

def main(argv):
    ''' Main method '''
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
        validate(inputdir, outputdir)
        walk(inputdir, outputdir)
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

        
def validate(inputdir, outputdir):
    ''' Validates input and output directories '''
    
    if len(inputdir) == 0 or len(outputdir) == 0:
        raise ValidationException("Must specify an input and an output.") 
    if os.path.realpath(inputdir) == os.path.realpath(outputdir):
        raise ValidationException("The input must be different from the output.")
    if not os.path.exists(inputdir):
        raise ValidationException("'{0}' does not exist.".format(inputdir))
    

def walk(inputroot, outputroot):
    ''' Walks input directory, creates output directory if needed '''
    
    print("Resizing...")
    # Counters for dirs, files and resized pictures
    count = { "dirs": 0, "files": 0, "resized": 0 }
    
    for inputdir, _, inputfiles in os.walk(inputroot):
        count["dirs"] += 1
        rel = os.path.relpath(inputdir, inputroot)
        outputdir = os.path.join(outputroot, rel)
        if not os.path.exists(outputdir):
            print("{0} does not exist, creating...".format(outputdir))
            os.makedirs(outputdir)
        for inputfile in inputfiles:
            # Skip hidden files
            if inputfile.startswith("."):
                continue
            inputpath = os.path.join(inputdir, inputfile)
            outputpath = os.path.join(outputdir, inputfile)
            count["files"] += 1
            if resize(inputpath, outputpath):
                count["resized"] += 1
               
    print("{0} directories, {1} files, {2} pictures resized.".format(count["dirs"], count["files"], count["resized"])) 
    print("Done.")
    
    
def resize(inputpath, outputpath):
    ''' Resizes one image, saves as JPG '''
    
    print("{0} - > {1}".format(inputpath, outputpath))
    if os.path.exists(outputpath):
        print("Already resized, skipping...")
        return False
    match = re.search("\(\d+\)\.jpg", inputpath)
    if match:
        print("Duplicate, skipping...")
        return
        
    t = str(magic.from_file(inputpath, mime=True))
    if t.find("image/jpeg") < 0:
        return False
    
    with Image(filename=inputpath) as img:
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
        img.save(filename=outputpath)
     
    return True


if __name__ == "__main__":
    main(sys.argv[1:])