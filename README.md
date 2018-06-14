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
This section defines the tests that should be performed for the script.

1. Regular expressions work as expected
    1. Add 3 files to a directory, *file1.txt*, *file2.txt*, *file3.txt*.
    1. *file1.txt* contains the line: `CS12345`
    1. *file3.txt* contains the line: `cs99999`
    1. Run script like so: `python findfiles.py "directory" "CS[0-9]" -v`
        1. Output should show that match was found in *file1.txt*, only 1 match in directory.
    1. Run script like so: `python findfiles.py "directory" "cs[0-9]" -v`
        1. Output should show that match was found in *file3.txt*, only 1 match in directory.
    1. Run script like so: `python findfiles.py "directory" "[Cc][Ss][0-9]" -v`
        1. Output should show that match was found in *file1.txt* and *file3.txt*, 2 matches in directory.
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
        * *file1.txt* under dir1, contains line: `person1@google.com`
        * *file2.txt* under dir4
        * *file3.txt* under dir5, contains line: `person3@uw.e`
        * *file4.txt* under dir6
        * *file5.txt* under dir6
        * *file6.txt* under dir8, contains line: `person4@yahoo.com`
        * *file7.txt* under dir8
        * *file8.txt* under dir8, contains line: `%person%-5-@udm.org`
    1. Run script like so: `python findfiles.py "directory" "[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}" -v`
        1. Output should show that match was found in *file1.txt*, *file6.txt* and *file8.txt*
1. Script still works when graphing package is not present
    1. Make sure the Python environment does *not* contain the package `matplotlib`
    1. Run script like so: `python findfiles.py "directory" "[Cc][Ss][0-9]" -g`. Directory should exist, doesn't matter if directory contains matches.
        1. Output should show matches found, and a message saying that the package `matplotlib` is not installed should appear, as well as instructions to install it.
1. Graphing functionality works as expected
    1. Use the same directory structure as the previous test case
    1. Run script like so: `python findfiles.py "directory" "[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}" -g`
        1. Output should show 1 match in *dir1* and 2 matches in *dir8*, and should generate a file called `matchfig.png` with a graph showing the matches per directory found.
1. Script with no arguments shows usage
    1. Run script like so: `python findfiles.py`
        1. Message showing how to use the script appears, and also tells user there are not enough arguments.
    1. Run script like so: `python findfiles.py "directory"`
        1. Message showing how to use the script appears, and also tells user there are not enough arguments.
1. Non-existing directory shows appropriate error
    1. Run script like so: `python findfiles.py "non-existing-directory" "[Cc][Ss][0-9]"`, making sure that the directory passed as argument does not exist.
        1. Message saying directory does not exist should appear.
1. Passing an existing file as starting directory shows appropriate error
    1. Run script like so: `python findfiles.py "file1.txt" "[Cc][Ss][0-9]"`, making sure that *file1.txt* is an existing file.
        1. Message saying root path is not a directory should appear.
1. Passing an invalid regular expression shows appropriate error
    1. Run script like so: `python findfiles.py "directory" "["`, making sure the directory passed as argument exists.
        1. Message saying regular expression is not valid should appear.
1. Unreadable files are handled appropriately and do not prevent finding other matches
    1. Create a test directory and add the files, *file1.txt*, *file2.txt*, *file3.txt*
    1. *file1.txt* contains the line: `CS12345`
    1. Change the permissions of *file2.txt* so that is not readable by the current user
        1. `chmod -r file2.txt` on Linux
        1. In Windows, right-click on the file in File Explorer, select `Properties`. Select the `Security` tab in the dialog that appears. Select your user in the list and then click the `Edit` permissions button. In the permissions dialog select your user again and check the `Read & execute` and `Read` checkboxes under the `Deny` column. Click `Ok` to dismiss both dialogs.
    1. Run script like so: `python findfiles.py "directory" "[Cc][Ss][0-9]"`
        1. Message saying that *file2.txt* could not be read appears, match is still found in *file1.txt*
1. Unreadable directories are handled appropriately and do not prevent finding other matches
    1. Create a test directory with the following structure:
        * testdir
            * subdir1
            * subdir2
    1. Add the following files:
        * *file1.txt* under subdir1, contains line: `CS12345`
        * *file2.txt* under subdir1
        * *file3.txt* under subdir2, contains line: `cs99999`
    1. Change permissions of *testdir/subdir2* so that is not readable by the current user
        1. `chmod -r subdir2` on Linux
        1. In Windows, right-click on *subdir2* in File Explorer, select `Properties`. Select the `Security` tab in the dialog that appears. Select your user in the list and then click the `Edit` permissions button. In the permissions dialog select your user again and check the `Read & execute`, `List folder contents` and `Read` checkboxes under the `Deny` column. Click `Ok` to dismiss both dialogs.
    1. Run script like so: `python findfiles.py "testdir" "[Cc][Ss][0-9]"`
        1. Message saying that *testdir/subdir2* could not be listed appears, match is still found in *file1.txt*
1. Large files are handled appropriately
    1. Create a very large text file, in the order of 500MB. Name it *file1.txt* and put it in a test directory. Make sure an email address appears as the last line in the file, while the rest of the file does not contain an email address.
    1. Run script like so: `python findfiles.py "directory" "[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}"`
        1. Script should be able to find the match in the large text file.
1. Binary files are handled appropriately
    1. Copy a binary file into a test directory
    1. Run script like so: `python findfiles.py "directory" "[Cc][Ss][0-9]"`
        1. Depending on the binary file a match might or might not be found, but it should not affect finding matches in other files.
1. If a worker process dies for any reason, the rest of the workers and results are not affected
    1. Create a very large text file, in the order of 500MB. Name it *file1.txt* and put it in a test directory.
    1. In the same directory create a file named *file2.txt* that contains the line `CS12345`
    1. Run script like so: `python findfiles.py "directory" "[Cc][Ss][0-9]"` (make sure the large text file does not contain a match)
    1. After some time (perhaps 20 seconds) kill the worker process that is reading the large text file
        1. In a machine with 4 processor cores with Linux, for example, the command `ps -a` will list 5 instances of `python` being executed. Two of them should be running, while three should be marked as `<defunct>`. The first of the running processes is probably the main process, so you should kill the other running process.
    1. After some time a message should appear saying that the script was not able to get expected results from the worker process. The match in *file1.txt* should appear in the results.

