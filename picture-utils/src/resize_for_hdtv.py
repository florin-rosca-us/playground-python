#!/opt/local/bin/python3

'''
Created on Jun 21, 2016

@author: Florin
'''
import re, math, collections, sys, getopt, os, magic
from wand.image import Image
from wand.display import display

Size = collections.namedtuple("Size", "width height")
SIZE = Size(1920, 1080)
RESOLUTION = Size(48, 48)


class ValidationException(Exception):
    def __init__(self,*args,**kwargs):
        Exception.__init__(self,*args,**kwargs)
       
        
'''
Main method.
'''
def main(argv):
    inputdir = ""
    outputdir = ""
    try:
        if len(argv) == 0:
            raise getopt.GetoptError("Must have at least one argument")    
        opts, args = getopt.getopt(argv, "hi:o:", ["help", "in=", "out="])
        for opt, arg in opts:
            if opt in ("-h", "help"):
                raise getopt.GetoptError("Help") 
            elif opt in ("-i", "in"):
                inputdir = arg
            elif opt in ("-o", "out"):
                outputdir = arg
        validate(inputdir, outputdir)
        walk(inputdir, outputdir)
    except getopt.GetoptError:
        print("Usage: scale.py -i <inputdir> -o <outputdir>")
        sys.exit(1)
    except ValidationException as ex:
        print("scale.py:", "".join(ex.args))
        sys.exit(2)

        
'''
Validates input and output directories.
'''
def validate(inputdir, outputdir):
    if len(inputdir) == 0 or len(outputdir) == 0:
        raise ValidationException("Must specify an input and an output.") 
    if os.path.realpath(inputdir) == os.path.realpath(outputdir):
        raise ValidationException("The input must be different from the output.")
    if not os.path.exists(inputdir):
        raise ValidationException("'{0}' does not exist.".format(inputdir))
    

'''
Walks input directory, creates output directory if needed.
'''
def walk(inputroot, outputroot):
    print("Scaling...")
    for inputdir, dirs, inputfiles in os.walk(inputroot):
        rel = os.path.relpath(inputdir, inputroot)
        outputdir = os.path.join(outputroot, rel)
        if not os.path.exists(outputdir):
            os.mkdir(outputdir)
        for inputfile in inputfiles:
            if inputfile.startswith("."):
                continue
            inputpath = os.path.join(inputdir, inputfile)
            outputpath = os.path.join(outputdir, inputfile)
            scale(inputpath, outputpath)
    print("Done.")
    
    
def scale(inputpath, outputpath):
    print("{0} - > {1}".format(inputpath, outputpath))
    if os.path.exists(outputpath):
        print("Already exists, skipping")
        return
    match = re.search("\(\d+\)\.jpg", inputpath)
    if match:
        print("Skipping duplicate: {0}".format(inputpath))
        return
        
    t = str(magic.from_file(inputpath, mime=True))
    if t.find("image/jpeg") < 0:
        return
    
    with Image(filename=inputpath) as img:
        print("Old size: {0}x{1}".format(img.width, img.height))
        img.resolution = RESOLUTION
        if img.width >= img.height:
            print("Horizontal")
            s = SIZE.width / img.width
            size = Size(int(img.width * s), int(img.height * s))   
            img.resize(size.width, size.height)
            # Height of a band to cut from the top and from the bottom of the picture
            y_crop = 0
            if size.height > SIZE.height:
                y_crop = int(math.ceil((size.height - SIZE.height) / 2))
                print("Crop: {0}".format(y_crop))  
                img.crop(0, y_crop, img.width, img.height - y_crop)
                            
        else:
            print("Vertical")
            s = SIZE.height / img.height
            size = Size(int(img.width * s), int(img.height * s))
            img.resize(size.width, size.height)
               
        print("New size: {0}x{1}".format(img.width, img.height)) 
        img.format = "jpeg"
        img.unsharp_mask(radius=2, sigma=1, amount=0.8, threshold=0.016)
        img.save(filename=outputpath)
     
        
if __name__ == "__main__":
    main(sys.argv[1:])