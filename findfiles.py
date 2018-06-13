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
config = {
    "keyword_pattern": re.compile(""),
    "root_path": "",
    "verbose": False,
    "generate_graph": False,
    "graph_size": [7, 5]
}


# Determine if given file is a match for keyword_pattern
def is_file_match(file_path, done_queue):
    try:
        line_count = 0
        with open(file_path, "r") as fi:
            line = fi.readline()

            while(not line == ""):
                if config["keyword_pattern"].search(line) is not None:
                    if config["verbose"]: print("Found match in file: " + file_path)

                    # Once a match has been found, no need to keep reading the file
                    return True

                line = fi.readline()
                line_count += 1
                if (line_count >= 100000):
                    # Send a 'keep alive' signal to gathering process.
                    # If the file we are scanning is very large, the gathering process
                    # might think the worker process died. Sending a signal every certain
                    # number of lines prevents this.
                    done_queue.put("---no match---")
                    line_count = 0
    except IOError as ioe:
        print("Error trying to read file: " + str(ioe))

    return False


# Recursively iterate through the directories and files in a directory,
# looking for matches to the regular expression
def find_files(path, task_queue):
    if config["verbose"]: print ("Looking in: " + path)
    try:
        for f in os.listdir(path):
            new_path = os.path.join(path, f)

            if os.path.isdir(new_path):
                find_files(new_path, task_queue)
            else:
                # Send actual file to worker Process to look for a match
                task_queue.put(new_path)
    except OSError as ose:
        print("Error trying to list directory: " + str(ose))


# Get results from worker Processes and collect them in our resulting
# dictionary
def gather_results(done_queue):
    done_count = 0
    cpu_count = multiprocessing.cpu_count()
    results = {}

    while True:
        try:
            result = done_queue.get(timeout=60)
        except Queue.Empty:
            print("Error: Did not get expected results from worker Process.")
            print("       Results might be incomplete.")
            break

        if result == "---stopped---":
            done_count += 1
            if done_count == cpu_count:
                # All worker Processes have stopped
                break
        elif not result == "---no match---":
            # We got a matching directory
            if results.has_key(result):
                results[result] += 1
            else:
                results[result] = 1

    return results


# Entry point for a worker Process
# Process a path from the task queue and put directory in output queue
# if a match is found.
def worker(worker_config, input, output):
    global config
    config = worker_config

    for file_path in iter(input.get, "---STOP---"):
        if is_file_match(file_path, output):
            dir_path = os.path.dirname(file_path)
            output.put(dir_path)
        else:
            # It is important for the worker Processes to indicate
            # when a match was _not_ found. The gathering process has a
            # timeout on the output queue, and assumes that one or more
            # worker Processes died if the output Queue times out. Indicating
            # that no match was found works then as a 'keep-alive' signal
            # that will prevent the timeout to happen in the case were a large
            # directory tree is being scanned where no match can be found.
            output.put("---no match---")
    
    output.put("---stopped---")


# Initialize worker Processes that will look for matches in files
def initialize_pool(task_queue, done_queue):
    # Create a Process for every processor in the machine.
    processors = multiprocessing.cpu_count()

    for i in range(processors):
        multiprocessing.Process(target=worker, args=(config, task_queue, done_queue)).start()


# Tell worker processes to stop looking for work
def terminate_pool(task_queue):
    processors = multiprocessing.cpu_count()

    for i in range(processors):
        task_queue.put("---STOP---")


# Validate arguments given to the script
def validate_arguments(root_path, keyword):
    try:
        config["keyword_pattern"] = re.compile(keyword)
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

    if args.verbose:
        config["verbose"] = True
    
    if args.graph:
        config["generate_graph"] = True
        config["graph_size"] = [args.graphx, args.graphy]

    keyword = args.keyword

    config["root_path"] = args.rootpath

    validate_arguments(config["root_path"], keyword)


# Generate graph with directory count data
def graph_data(matches):
    if not config["generate_graph"]:
        return

    if not graph_support:
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

    graph_size = config["graph_size"]
    fig, ax = plt.subplots(figsize=(graph_size[0], graph_size[1]))

    index = np.arange(n_groups)
    bar_width = 0.7

    opacity = 0.8
    error_config = {"ecolor": "0.3"}

    ax.bar(index, matches_data, bar_width,
           alpha=opacity, color="b",
           error_kw=error_config,
           label="Match Count")

    ax.set_xlabel("Directories")
    ax.set_ylabel("Match Count")
    ax.set_title("Matches by directory")
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


# Print resulting matches
def print_result(matches):
    print("Matches:")
    if (len(matches) == 0):
        print("No matches found.")
    else:
        for key in enumerate(matches.keys()):
            print(key[1] + ": " + str(matches[key[1]]))


def main():
    """ Main method of the script.
        - validate parameters
        - set any requested options
        - start directory traversal
        - generate graph if necessary """

    task_queue = multiprocessing.Queue()
    done_queue = multiprocessing.Queue()

    parse_arguments()
    initialize_pool(task_queue, done_queue)
    find_files(config["root_path"], task_queue)
    terminate_pool(task_queue)
    matches = gather_results(done_queue)
    print_result(matches)
    graph_data(matches)


# Starting point of the script
if __name__ == "__main__":
    multiprocessing.freeze_support()
    main()
