#!/usr/bin/python
import argparse
import multiprocessing
import os
import Queue
import re
import sys

graph_support = True

try:
    import numpy as np
    import matplotlib.pyplot as plt
    from matplotlib.ticker import MaxNLocator
    from collections import namedtuple
except ImportError:
    graph_support = False
    

# Global variables
keyword_pattern = re.compile("")
root_path = ""
verbose = False
generate_graph = False
graph_size = [7, 5]
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
    results = {}

    while (True):
        try:
            result = done_queue.get(timeout=10)
        except Queue.Empty:
            print("Error: Did not get expected results from worker Process.")
            print("       Results might be incomplete.")
            break

        if result == "---stopped---":
            done_count += 1
            if done_count == cpu_count:
                break
        else:
            # We got a matching directory
            if (results.has_key(result)):
                results[result] += 1
            else:
                results[result] = 1

    return results


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
    parser.add_argument("-gx", "--graphx", type=int, default=7, help="size of graph in X axis")
    parser.add_argument("-gy", "--graphy", type=int, default=5, help="size of graph in Y axis")
    parser.add_argument("rootpath", help="directory where scanning will begin")
    parser.add_argument("keyword", help="regular expression that defines keyword to search in files")
    args = parser.parse_args()

    if (args.verbose):
        global verbose
        verbose = True
    
    if (args.graph):
        global generate_graph
        generate_graph = True
        global graph_size
        graph_size = [args.graphx, args.graphy]

    keyword = args.keyword

    global root_path
    root_path = args.rootpath

    validate_arguments(root_path, keyword)


# Generate graph with directory count data
def graph_data(matches):
    if (not generate_graph):
        return

    if (not graph_support):
        print("This script uses the package 'matplotlib' to generate graphs.")
        print("Please run the following command to install matplotlib:")
        print("")
        print("pip install -U matplotlib")
        print("")
        quit()

    n_groups = len(matches)

    matches_data = []
    matches_labels = []
    for item in matches.items():
        matches_labels.append(item[0])
        matches_data.append(item[1])

    fig, ax = plt.subplots(figsize=(graph_size[0], graph_size[1]))

    index = np.arange(n_groups)
    bar_width = 0.7

    opacity = 0.8
    error_config = {'ecolor': '0.3'}

    ax.bar(index, matches_data, bar_width,
           alpha=opacity, color='b',
           error_kw=error_config,
           label="Match Count")

    ax.set_xlabel('Directories')
    ax.set_ylabel('Match Count')
    ax.set_title('Matches by directory')
    ax.set_xticks(index)
    ax.set_xticklabels(matches_labels)
    ax.legend()

    # Since we have directory names as labels, rotate them
    # so they become legible.
    plt.xticks(rotation=90)

    try:
        fig.tight_layout()
        plt.savefig("matchfig")
        print("Graph has been saved to file 'matchfig.png'")
    except ValueError as valerr:
        print("Error generating graph: " + str(valerr))
        print("Current figure size is: " + str(graph_size))
        print("Try specifying a larger figure size.")


def main():
    """ Main method of the script.
        - validate parameters
        - set any requested options
        - start directory traversal
        - generate graph if necessary """

    parse_arguments()
    initialize_pool()
    find_files(root_path)
    terminate_pool()
    matches = gather_results()
    graph_data(matches)

    print("Matches:")
    if (len(matches) == 0):
        print("No matches found.")
    else:
        for key in enumerate(matches.keys()):
            print(key[1] + ": " + str(matches[key[1]]))
    
# Starting point of the script
if __name__ == "__main__":
    multiprocessing.freeze_support()
    main()