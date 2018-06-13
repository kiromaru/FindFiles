# FindFiles
This is a script that recursively iterates from a starting directory, and counts the number of files in a subdirectory that match a given regular expression.

The matches found are printed to the screen when the script is done running.

## Argument Handling
`argparse` is used to parse arguments to the script. Arguments are accepted to specify the directory where scanning will start, as well as the regular expression that must match in the files.

## Portability
The code was tested in Ubuntu 16.04 with Python 2.7.12, and in Windows 10 with Python 2.7.15. The code does not make any assumption about the operating system. When joining file paths, for example, `os.path.join` is used instead of manually concatenating strings.

## Scalability
The code is designed to be scalable by using worker processes to perform the search of a regular expression in a given file. The main process spawns a pool of workers. The main process is responsible for looking for files to scan (scanning the directory structure), and providing the full path to the files to scan to the worker processes. After walking through the existing directories, the main process is then responsible for gathering the results of whether a file matches the given regular expression or not, and collecting them in a dictionary.

## Reliability
The code is designed to handle errors, and continue working if possible. The parameters are validated at the beginning, to ensure they make sense. Places where things can fail (reading a file, scanning a directory, waiting for results of worker processes) are protected by handling the possible errors that might happen.

## Tests
This section defines the tests performed for the script:

1. Regular expressions work as expected
    1. Add 3 files to a directory, file1.txt, file2.txt, file3.txt.
    1. file1.txt contains the line: `CS12345`
    1. file3.txt contains the line: `cs99999`
    1. Run script like so: `python findfiles.py "directory" "CS[0-9]" -v`
        1. Output should show that match was found in file1.txt, only 1 match in directory.
    1. Run script like so: `python findfiles.py "directory" "cs[0-9]" -v`
        1. Output should show that match was found in file3.txt, only 1 match in directory.
    1. Run script like so: `python findfiles.py "directory" "[Cc][Ss][0-9]" -v`
        1. Output should show that match was found in file1.txt and file3.txt, 2 matches in directory.
1. Recursion works as expected
    1. Create the following directory structure under a test directory:
        * dir1
        * dir2
            * dir4
            * dir5
        * dir3
            * dir6
                * dir7
                * dir8
    1. Add the following files:
        * file1.txt under dir1, contains line: `person1@google.com`
        * file2.txt under dir4
        * file3.txt under dir5, contains line: `person3@uw.edu`     
        * file4.txt under dir6
        * file5.txt under dir6
        * file6.txt under dir8, contains line: `person4@yahoo.com`
        * file7.txt under dir8
        * file8.txt under dir8, contains line: `person5@udm.org`
    1. Run script like so: `python findfiles.py "directory" "[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}" -v`
        1. Output should show that match was found in file1.txt, file3.txt, file6.txt and file8.txt
