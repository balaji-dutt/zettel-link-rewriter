#!/usr/bin/env python

import logging
import pathlib
import configargparse
import re
import time

# Configure logging early
logging.basicConfig(level=logging.DEBUG,
                    format="%(asctime)s %(levelname)-8s %(funcName)s():%(lineno)i:        %(message)s",
                    datefmt="%Y-%m-%d %H:%M:%S")


def parse_config():
    default_config = pathlib.PurePath(__file__).stem + ".ini"
    config = configargparse.ArgParser(default_config_files=[default_config])
    config.add_argument('-c', '--config', is_config_file=True,
                        help="Specify path to Configuration file. Default is " +
                             pathlib.PurePath(__file__).stem + ".ini", metavar='CONFIG'
                        )
    config.add_argument('-v', '--verbosity', action='store',
                        help="Specify logging level for script. Default is %(default)s.",
                        choices=['warning', 'info', 'debug'],
                        default='warning')
    config.add_argument('-f', '--file', action='store',
                        help='Write log messages to a file', metavar='LOGFILE')
    config.add_argument('--source_files', action='store',
                        help="Specify path to directory containing source markdown files. Default is current directory."
                        , default=pathlib.PurePath(__file__).parent, metavar='DIRECTORY')
    config.add_argument('--target_files', action='store',
                        help="Specify path to directory containing source markdown files. Default is to use a "
                             "\"dest\" folder in the current directory. "
                        , default=pathlib.Path.joinpath(pathlib.PurePath(__file__).parent, "dest"), metavar='DIRECTORY')
    config.add_argument('-p', '--process', action='store',
                        help="Determine whether to process all source files or only recently modified files. Default "
                             "is %(default)s.",
                        choices=['all', 'modified'],
                        default='all')
    config.add_argument('-m', '--modified', action='store', type=int,
                        help="Specify in minutes what is the time limit for recently modified files. Default is "
                             "%(default)s."
                        , default=60, metavar='MINUTES')
    options = config.parse_known_args()
    # Convert tuple of parsed arguments into a dictionary. There are two values within this tuple.
    # [0] represents recognized arguments. [1] represents unrecognized arguments on command-line or config file.
    option_values = vars(options[0])
    # Assign dictionary values to variables.
    config_file = option_values.get("config")
    source_files = option_values.get("source_files")
    target_files = option_values.get("target_files")
    logging_level = option_values.get("verbosity")
    log_file = option_values.get("file")
    process_type = option_values.get("process")
    modified_time = option_values.get("modified")

    # Reset logging levels as per config
    logger = logging.getLogger()
    logger.setLevel(logging_level.upper())

    # Configure file-based logging
    if log_file is None:
        logging.debug("No log file set. All log messages will print to Console only")
    else:
        filelogger = logging.FileHandler("{0}".format(log_file))
        filelogformatter = logging.Formatter(
            '%(asctime)s %(levelname)-8s %(funcName)s():%(lineno)i:        %(message)s',
            datefmt="%Y-%m-%d %H:%M:%S")
        filelogger.setFormatter(filelogformatter)
        logger.addHandler(filelogger)
        logging.warning("Outputting to log file")

    # Check if specified config file exists else bail
    if config_file is None:
        config_file = default_config
        logging.debug("No configuration file specified. Using the default configuration file %s", default_config)
    elif pathlib.Path(config_file).exists():
        logging.debug("Found configuration file %s", config_file)
    else:
        logging.exception('Did not find the specified configuration file %s', config_file)
        raise FileNotFoundError

    # Check if somehow modified_time is set to NIL when processing modified files.
    if process_type == 'modified' and not modified_time:
        raise ValueError("Script is set to process only recently modified files. But the modified time parameter is "
                         "incorrectly defined.")

    # Print values of other parameters in debug mode
    if process_type == 'all' and modified_time:
        logging.debug("Script is set to process all files. Modified time parameter (if any) will have no effect.")
    elif process_type == 'modified' and modified_time:
        logging.debug("Script is set to only process files modified in last %s minutes", modified_time)

    return config_file, source_files, target_files, log_file, process_type, modified_time


def check_dirs(source_dir, target_dir):
    """
    Function to check if specified directories exist. The function will create the destination directory if it does
    exist.

    :param source_dir: Directory containing files to be processed.
    :param target_dir: Directory to store files after they are processed.
    :return: Directory paths
    """
    if source_dir == str(pathlib.Path.joinpath(pathlib.Path(__file__).parent, "source")) and pathlib.Path(
            source_dir).exists():
        print('No source directory found in specified configuration file. Using default {} instead'.format(source_dir))
    elif pathlib.Path(source_dir).exists():
        pass
    else:
        logging.exception('Did not find the directory %s', source_dir)
        raise NotADirectoryError

    if target_dir == str(pathlib.Path.joinpath(pathlib.Path(__file__).parent, "dest")):
        print('No target directory found in specified configuration file. Using default {} instead'.format(target_dir))
        pathlib.Path(target_dir).mkdir(exist_ok=True)
        # exist_ok=True will function like mkdir -p so there is no need to wrap this in a try-except block.
    elif pathlib.Path(target_dir).exists():
        pass
    else:
        print('Did not find the target directory {}. Will try create it now'.format(target_dir))
        pathlib.Path(target_dir).mkdir(exist_ok=True)

    return [source_dir, target_dir]


def modify_links(file_obj):
    """
    Function will parse file contents (opened in utf-8 mode) and modify standalone [[wikilinks]] and in-line
    [[wikilinks]](wikilinks) into traditional Markdown link syntax.

    :param file_obj: Path to file
    :return: List object containing modified text. Newlines will be returned as '\n' strings.
    """

    file = file_obj
    linelist = []
    logging.debug("Going to open file %s for processing now.", file)
    try:
        with open(file, encoding="utf8") as infile:
            for line in infile:
                linelist.append(re.sub(r"(\[\[)((?<=\[\[).*(?=\]\]))(\]\])(?!\()", r"[\2](\2.md)", line))
                # Finds  references that are in style [[foo]] only by excluding links in style [[foo]](bar).
                # Capture group $2 returns just foo
                linelist_final = [re.sub(r"(\[\[)((?<=\[\[)\d+(?=\]\]))(\]\])(\()((?!=\().*(?=\)))(\))",
                                         r"[\2](\2 \5.md)", line) for line in linelist]
                # Finds only references in style [[foo]](bar). Capture group $2 returns foo and capture group $5
                # returns bar
    except EnvironmentError:
        logging.exception("Unable to open file %s for reading", file)
    logging.debug("Finished processing file %s", file)
    return linelist_final


def write_file(file_contents, file, target_dir):
    """
    Function will take modified contents of file from modify_links() function and output to target directory. File
    extensions are preserved and file is written in utf-8 mode.

    :param file_contents: List object containing modified text.
    :param file: Path to source file. Will be used to construct target file name.
    :param target_dir: Path to destination directory
    :return: Full path to file that was written to target directory.
    """
    name = pathlib.PurePath(file).name
    fullpath = pathlib.PurePath(target_dir).joinpath(name)
    logging.debug("Going to write file %s now.", fullpath)
    try:
        with open(fullpath, 'w', encoding="utf8") as outfile:
            for item in file_contents:
                outfile.write("%s" % item)
    except EnvironmentError:
        logging.exception("Unable to write contents to %s", fullpath)

    logging.debug("Finished writing file %s now.", fullpath)
    return fullpath


def process_files(source_dir, target_dir, process_type, modified_time):
    """
    Function to process input files. Will operate in a loop on all files (process "all")
    or recently modified files (process "modified")

    :param source_dir: Path to directory containing files to be processed.
    :param target_dir: Path to directory where files should be written to after processing.
    :param process_type: Flag to process all or only modified files.
    :param modified_time: Time window for finding recently modified files.
    :return: Number of files processed.
    """
    count = 0

    if process_type == 'all':
        logging.debug("Start processing all files in %s", source_dir)
        for count, file in enumerate(pathlib.Path(source_dir).glob('*.*'), start=1):
            # We will not use iterdir() here since that will descend into sub-directories which may have
            # unexpected side-effects
            modified_text = modify_links(file)
            # Return values can only be obtained in the calling function and are captured by
            # calling the function while assigning to a variable.
            write_file(modified_text, file, target_dir)
            # writer_dummy(regex_dummy(file))
            # Short-hand way of calling one function with the return value of another.
    elif process_type == 'modified':
        logging.debug("Start processing recently modified files in %s", source_dir)
        for count, file in enumerate(pathlib.Path(source_dir).glob('*.*'), start=1):
            if pathlib.Path(file).stat().st_mtime > time.time() - modified_time * 60:
                modified_text = modify_links(file)
                write_file(modified_text, file, target_dir)
    logging.debug("Finished processing all files in %s", source_dir)

    return count


def main():
    start_time = time.perf_counter()
    parameters = parse_config()
    check_dirs(source_dir=str(parameters[1]), target_dir=str(parameters[2]))
    count = process_files(source_dir=str(parameters[1]), target_dir=str(parameters[2]), process_type=parameters[4],
                          modified_time=parameters[5])
    end_time = time.perf_counter()
    elapsed_time = end_time - start_time
    hours, remainder = divmod(elapsed_time, 3600)
    minutes, seconds = divmod(remainder, 60)
    print("Script took {:02}:{:02}:{:02}".format(int(hours), int(minutes), int(seconds)), "to process {0} files"
          .format(count))


if __name__ == '__main__':
    main()
