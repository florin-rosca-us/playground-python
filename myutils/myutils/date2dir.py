"""
Creates sub-directories in the format yyy.mm.dd under the specified output directory and moves files from the specified input directory according to creation dates.
The output directory can be the same as the input directory. Skips files starting with dot.

Created on Oct 25, 2016

@author: Florin Rosca
"""

import sys, os, getopt, time

SCRIPT = os.path.basename(__file__)

def main(argv):
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
        if not output_dir:
            output_dir = input_dir
        date2dir(input_dir, output_dir)
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


def _accept(dir_, file):
    """ Returns True if the file should be processed, False if not. """
    if file.startswith("."):
        return False
    return True
            
            
def _created(path):
    """ Returns a string yyyy.mm.dd """
    t = os.path.getmtime(path)
    return time.strftime("%Y.%m.%d", time.localtime(t))


def date2dir(input_dir, output_dir):
    """ Moves files to sub-directories of output_dir named "yyyy.mm.dd """
    paths = []
    
    # Build the list of files to move
    for f in os.listdir(input_dir):
        if not _accept(input_dir, f):
            continue
        p = os.path.join(input_dir, f)
        if os.path.isfile(p):
            paths.append(p)
            
    # Move files
    for p in paths:
        name = _created(p)
        subdir = os.path.join(output_dir, name)
        print(subdir)
        if not os.path.exists(subdir):
            os.mkdir(subdir)
        renamed = os.path.join(output_dir, name, os.path.basename(p))
        print("{0} -> {1}".format(p, renamed))    
        os.rename(p, renamed)

    
if __name__ == "__main__":
    main(sys.argv[1:])
    