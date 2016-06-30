'''
Created on Jun 30, 2016

@author: Florin
'''
import sys, os, getopt, math, shutil


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
    
    
def accept(dir, file):
    if file.startswith("."):
        return False
    if not file.lower().endswith(".jpg"):
        return False
    return True
    
    
def walk(inputroot, outputroot):
    ''' Walks input directory, creates output directory if needed '''
    count = { "dirs": 0, "files": 0, "moved": 0 }
    
    # Count files to copy to determine number of padding zeros
    for dirpath, dirs, files in os.walk(inputroot):
        if os.path.samefile(inputroot, dirpath):
            continue
        for file in files:
            if not accept(dirpath, file):
                continue
            count["files"] += 1
    print("Count: {0}".format(count["files"]))  
    zeros = int(math.ceil(math.log10(count["files"])))
    print("Zeros: {0}".format(zeros))   

    if not os.path.exists(outputroot):
        print("{0} does not exist, creating...".format(outputroot))
        os.makedirs(outputroot)
            
    # Copy files under output root with new name   
    i = 0 
    for dirpath, _, files in os.walk(inputroot):
        count["dirs"] += 1
        for file in files:
            if not accept(dirpath, file):
                continue
            
            inputpath = os.path.join(dirpath, file)
            _, inputext = os.path.splitext(inputpath)
            i += 1
            outputfile = str(i).zfill(zeros) + inputext 
            outputpath= os.path.join(outputroot, outputfile)
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