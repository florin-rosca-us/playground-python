"""
Moves files from an input directory to sub-directories yyy.mm.dd corresponding to file creation dates.
Skips files starting with dot.

Created on Oct 25, 2016

@author: Florin Rosca
"""

import sys, os, getopt, time

SCRIPT = os.path.basename(__file__)

def main(argv):
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
                
        if not outputdir:
            outputdir = inputdir
         
        date2dir(inputdir, outputdir)
            
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
        

def date2dir(inputdir, outputdir):
    """ Moves files to sub-directories of outputdir named "yyyy.mm.dd """
    paths = []
    
    # Build the list of files to move
    for f in os.listdir(inputdir):
        if f.startswith("."):
            continue
        p = os.path.join(inputdir, f)
        if os.path.isfile(p):
            paths.append(p)
            
    # Move files
    for p in paths:
        name = created(p)
        subdir = os.path.join(outputdir, name)
        print(subdir)
        if not os.path.exists(subdir):
            os.mkdir(subdir)
        renamed = os.path.join(outputdir, name, os.path.basename(p))
        print("{0} -> {1}".format(p, renamed))    
        os.rename(p, renamed)



def created(path):
    """ Returns a string yyyy.mm.dd """
    t = os.path.getmtime(path)
    return time.strftime("%Y.%m.%d", time.localtime(t))
    
if __name__ == "__main__":
    main(sys.argv[1:])
    