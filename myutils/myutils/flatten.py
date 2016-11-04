"""
Copies JPEG files from the input directory and its sub-directories recursively to the specified output directory.

TODO: Specify what to move.

Created on Jun 30, 2016

@author: Florin Rosca
"""

import sys, os, getopt, math, shutil


SCRIPT = os.path.basename(__file__)

class ValidationException(Exception):
    """ An exception throws when a validation error occurs """
    def __init__(self,*args,**kwargs):
        Exception.__init__(self,*args,**kwargs)
        
      
def main(argv):
    """ Main method """
    input_dir = ""
    output_dir = ""
    try:
        if len(argv) == 0:
            raise getopt.GetoptError("Must have at least one argument") 
        opts, _ = getopt.getopt(argv, "hi:o:", ["help", "in=", "out="])
        for opt, arg in opts:
            if opt in ("-h", "--help"):
                raise getopt.GetoptError("Help") 
            elif opt in ("-i", "--in"):
                input_dir = arg
            elif opt in ("-o", "--out"):
                output_dir = arg
        flatten(input_dir, output_dir)
    except getopt.GetoptError:
        print("USAGE: {0} <options>".format(SCRIPT))
        print("")
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
    """ Validates input and output directories, throws a ValidateException if invalid. """
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
    if not file.lower().endswith(".jpg"):
        return False
    return True
    
    
def flatten(input_dir, output_dir):
    """ Walks input directory, creates output directory if needed """
    _validate(input_dir, output_dir)
    count = { "dirs": 0, "files": 0, "moved": 0 }
    
    # Count files to copy to determine number of padding zeros
    for dirpath, _, files in os.walk(input_dir):
        if os.path.samefile(input_dir, dirpath):
            continue
        for file in files:
            if not _accept(dirpath, file):
                continue
            count["files"] += 1
    print("Count: {0}".format(count["files"]))  
    zeros = int(math.ceil(math.log10(count["files"])))
    print("Zeros: {0}".format(zeros))   

    if not os.path.exists(output_dir):
        print("{0} does not exist, creating...".format(output_dir))
        os.makedirs(output_dir)
            
    # Copy files under output root with new name   
    i = 0 
    for dirpath, _, files in os.walk(input_dir):
        count["dirs"] += 1
        for file in files:
            if not _accept(dirpath, file):
                continue
            
            inputpath = os.path.join(dirpath, file)
            _, inputext = os.path.splitext(inputpath)
            i += 1
            outputfile = str(i).zfill(zeros) + inputext 
            outputpath= os.path.join(output_dir, outputfile)
            print("{0} -> {1}".format(inputpath, outputpath))
            if os.path.exists(outputpath):
                print("Already exists")
                continue
            
            shutil.copy2(inputpath, outputpath)
            count["moved"] += 1

    print("{0} directories, {1} files, {2} files moved.".format(count["dirs"], count["files"], count["moved"])) 
    print("Done.")
    
       
if __name__ == "__main__":
    main(sys.argv[1:])