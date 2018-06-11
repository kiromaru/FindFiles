#!/usr/bin/python
import argparse
import multiprocessing
import os
import re
import sys

# Global variables
keyword_pattern = re.compile("")
root_path = ""
directory_matches = {}
verbose = False
generate_graph = False
task_queue = multiprocessing.Queue()
done_queue = multiprocessing.Queue()


# Determine if given file is a match for keyword_pattern
def is_file_match(file_path):
    try:
        with open(file_path, "r") as fi:
            line = fi.readline()

            while(not line == ""):
                if keyword_pattern.search(line) is not None:
                    if verbose: print("Found match in file: " + file_path)

                    # Once a match has been found, no need to keep reading the file
                    return True

                line = fi.readline()
    except IOError as ioe:
        print("Error trying to read file: " + str(ioe))

    return False


# Recursively iterate through the directories and files in a directory,
# looking for matches to the regular expression
def find_files(path):
    if verbose: print ("Looking in: " + path)
    try:
        for f in os.listdir(path):
            new_path = os.path.join(path, f)

            if os.path.isdir(new_path):
                find_files(new_path)
            else:
                # Send actual file to worker Process to look for a match
                task_queue.put(new_path)
    except OSError as ose:
        print("Error trying to list directory: " + str(ose))


# Get results from worker Processes and collect them in our resulting
# dictionary
def gather_results():
    done_count = 0
    cpu_count = multiprocessing.cpu_count()

    while (True):
        result = done_queue.get(timeout=5)
        if result == "---stopped---":
            done_count += 1
            if done_count == cpu_count:
                break
        else:
            # We got a matching directory
            if (directory_matches.has_key(result)):
                directory_matches[result] += 1
            else:
                directory_matches[result] = 1


# Entry point for a worker Process
# Process a path from the task queue and put directory in output queue
# if a match is found.
def worker(input, output):
    for path in iter(input.get, "---STOP---"):
        if (is_file_match(path)):
            dir_path = os.path.dirname(path)
            output.put(dir_path)
    
    output.put("---stopped---")


# Initialize worker Processes that will look for matches in files
def initialize_pool():
    # Create a Process for every processor in the machine.
    processors = multiprocessing.cpu_count()

    for i in range(processors):
        multiprocessing.Process(target=worker, args=(task_queue, done_queue)).start()


# Tell worker processes to stop looking for work
def terminate_pool():
    processors = multiprocessing.cpu_count()

    for i in range(processors):
        task_queue.put("---STOP---")


# Validate arguments given to the script
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


# Parse arguments given to the script
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

    parse_arguments()
    initialize_pool()
    find_files(root_path)
    terminate_pool()
    gather_results()

    print("Matches:")
    if (len(directory_matches) == 0):
        print("No matches found.")
    else:
        for key in enumerate(directory_matches.keys()):
            print(key[1] + ": " + str(directory_matches[key[1]]))

# Starting point of the script
if __name__ == "__main__":
    multiprocessing.freeze_support()
    main()
