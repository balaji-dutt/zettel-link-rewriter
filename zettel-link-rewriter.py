#!/usr/bin/env python

import os
import logging
import pathlib
import configargparse

# Defining variables
src_dir = pathlib.Path("F:/Balaji/Development/zettel-link-rewriter/source")
target_dir = pathlib.Path("F:/Balaji/Development/zettel-link-rewriter/target")

# Configure logging early
logging.basicConfig(level=10,  # DEBUG by default
                    format="%(asctime)s %(levelname)-8s %(funcName)s():%(lineno)i:        %(message)s",
                    datefmt="%Y-%m-%d %H:%M:%S")


# def someFunc(myList = [], *args):
#     for x in myList:
#         print(x)
#
# items = [1,2,3,4,5]
#
# someFunc(items)

def parse_config():
    default_config = pathlib.PurePath(__file__).stem + ".ini"
    config = configargparse.ArgParser(default_config_files=[default_config])
    config.add_argument('-c', '--config', is_config_file=True,
                        help="Specify path to Configuration file. Default is " +
                             pathlib.PurePath(__file__).stem + ".ini", metavar="CONFIG"
                        )
    config.add_argument('-v', '--verbosity', action='store',
                        help="Specify logging level for script. Default is %(default)s.",
                        choices=['warning', 'info', 'debug'],
                        default="warning")
    config.add_argument('-f', '--file', action='store',
                        help='Write log messages to a file', metavar='LOGFILE')
    config.add_argument('--source_files', action='store',
                        help='Specify path to directory containing source markdown files. Default is current directory.'
                        , default=pathlib.PurePath(__file__).parent)
    config.add_argument('--target_files', action='store',
                        help='Specify path to directory containing source markdown files. Default is current directory.'
                        , default=pathlib.Path.joinpath(pathlib.PurePath(__file__).parent, "dest"))
    options = config.parse_known_args()
    # Convert tuple of parsed arguments into a dictionary. There are two values within this tuple.
    # [0] represents recognized arguments. [1] represents unrecognized arguments on command-line or config file.
    option_values = vars(options[0])
    # Assign dictionary values to variables.
    global source_files
    global target_files
    global log_file
    config_file = option_values.get("config")
    source_files = option_values.get("source_files")
    target_files = option_values.get("target_files")
    logging_level = option_values.get("verbosity")
    log_file = option_values.get("file")

    # Reset logging levels
    logger = logging.getLogger()
    logger.setLevel(logging_level.upper())

    # Check if specified config file exists else bail
    try:
        pathlib.Path(config_file).exists()
    except:
        logging.exception('Did not find the specified configuration file %s', config_file)
        raise FileNotFoundError
    else:
        if config_file == default_config:
            logging.debug("Using the default configuration file %s", default_config)
        else:
            logging.debug("Found configuration file %s", config_file)

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


def check_dir(*args):
    for item in args:
        # print(item)
        if os.path.isdir(item):
            pass
        else:
            logging.exception('Did not find the directory %s', item)
            raise NotADirectoryError

def main():
    parse_config()
    # dir_list = [src_dir, target_dir]
    # check_dir(*dir_list)


if __name__ == '__main__':
    main()
