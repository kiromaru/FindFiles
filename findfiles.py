#!/usr/bin/python
import argparse
import os
import re
import sys
from multiprocessing import Process, freeze_support

# Global variables
keyword_pattern = re.compile("")
root_path = ""
directory_matches = {}
verbose = False
generate_graph = False


def check_file_match(file_path):
    try:
        with open(file_path, "r") as fi:
            line = fi.readline()

            while(not line == ""):
                if keyword_pattern.search(line) is not None:
                    if verbose: print("Found match in file: " + file_path)
                    dir_path = os.path.dirname(file_path)

                    if (directory_matches.has_key(dir_path)):
                        directory_matches[dir_path] = directory_matches[dir_path] + 1
                    else:
                        directory_matches[dir_path] = 1

                    # Once a match has been found, no need to keep reading the file
                    return

                line = fi.readline()
    except IOError as ioe:
        print("Error trying to read file: " + str(ioe))


def find_files(path):
    if verbose: print ("Looking in: " + path)
    try:
        for f in os.listdir(path):
            new_path = os.path.join(path, f)

            if os.path.isdir(new_path):
                find_files(new_path)
            else:
                check_file_match(new_path)
    except OSError as ose:
        print("Error trying to list directory: " + str(ose))


def validate_arguments(root_path, keyword):
    try:
        global keyword_pattern
        keyword_pattern = re.compile(keyword)
    except re.error as ree:
        print("Error: given regular expression is not valid: " + str(ree))
        quit()

    if not os.path.isdir(root_path):
        print("Error: Given root path is not a directory: " + root_path)
        quit()

    if not os.path.exists(root_path):
        print("Error: Given root path does not exist: " + root_path)
        quit()


def parse_arguments():
    parser = argparse.ArgumentParser(description="Count number of files in a given directory that match a regular expression")
    parser.add_argument("-v", "--verbose", help="set verbose output", action="store_true")
    parser.add_argument("-g", "--graph", help="generate graph of directory counts", action="store_true")
    parser.add_argument("rootpath", help="directory where scanning will begin")
    parser.add_argument("keyword", help="regular expression that defines keyword to search in files")
    args = parser.parse_args()

    if (args.verbose):
        global verbose
        verbose = True
    
    if (args.graph):
        global generate_graph
        generate_graph = True

    keyword = args.keyword

    global root_path
    root_path = args.rootpath

    validate_arguments(root_path, keyword)


def main():
    """ Main method of the script.
        - validate parameters
        - set any requested options
        - start directory traversal """
    # Validate parameters and set options
    parse_arguments()

    # Start directory traversal
    find_files(root_path)

    print("Matches:")
    if (len(directory_matches) == 0):
        print("No matches found.")
    else:
        for key in enumerate(directory_matches.keys()):
            print(key[1] + ": " + str(directory_matches[key[1]]))

# Starting point of the script
if __name__ == "__main__":
    #freeze_support()
    #p = Process(target=main)
    #p.start()

    main()
