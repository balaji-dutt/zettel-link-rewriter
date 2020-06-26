## Rewrite Wikilinks in your Zettelkasten as Markdown Links

This repository contains a Python script that can take a folder of Markdown files (or any other compatible format) and 
convert any links that are in `[[wikilink]]` format into the standard Markdown link format.

### Why?
Most Zettelkasten software today will handle linking between different notes by adding a link using the `[[wikilink]]`
syntax. This is great for reading and writing within the Zettelkasten ecosystem but almost no standard Markdown renderer
will automatically recognize the `[[wikilink]]` syntax. This script attempts to give you more inter-operability with 
other Markdown software by converting `[[wikilinks]]` into standard Markdown `[wikilink](wikilink)` syntax. 

### Features
- Fully cross-platform. Script was developed in a Windows environment and is extensively tested to work in 
Windows.
- Provides a number of parameters to configure the script. Parameters can be specified either on the command-line or 
via a configuration file. Refer to [zettel_link_rewriter.ini](zettel_link_rewriter.ini) to see an example.
- Handles links within Markdown code blocks correctly, i.e., does not rewrite them. This includes fenced code blocks, 
inline code snippets and code blocks indented with four spaces. Do note the [Caveats](#caveats) though.
- Minimal dependencies. The script requires only one additional package to be installed (which is because Python's 
built-in `argparse` module is _terrible_.)

### Dependencies
- Python 3.4 or higher (Script has only been tested with Python 3.8)
- List of packages specified in `requirements.txt`

### Getting Started
You can use this script by cloning the repo and installing Python and the script dependencies in a Python venv.
```shell
git clone https://github.com/balaji-dutt/zettel-link-rewriter.git
python -m venv .venv
./venv/scripts/activate
pip install -r requirements.txt
python zettel_link_rewriter.py
```
Running the script as shown above will make the script run with a set of built-in defaults. But you can configure 
the script either by supplying a list of parameters on the command-line:
```shell
python zettel_link_rewriter.py -v debug -p all --target_files ./dest/
```

Or you can configure the script by passing a path to a configuration file:

```shell
python zettel_link_rewriter.py -c myconfig.ini
```

An explanation of the different parameters the script recognizes are provided below.

### Parameters

|Parameter|Mandatory|Description|
|---------|---------|-----------|
|`-h`|No|Show a help message|
|`-c` / `--config`|No|Specify path to Configuration file. <br>By default, the script will look for a configuration file named zettel_link_rewriter.ini in the same directory|
|`-v`|No|Verbosity option. Configures the logging level for the script. You can specify 3 levels of verbosity - `warning/info/debug`. The default is `warning`|
|`-f` / `--file`|No|Write log messages to a file instead of on the console.|
|`--source_files`|No|Specify path to directory containing source markdown files to be processed. <br> Default is to use a "source" folder in the current directory.|
|`--target_files`|No|Specify path to directory where processed markdown files should be saved. <br> Default is to use a "dest" folder in the current directory. <br> The folder where markdown files should be saved after processing will be created if it does not exist.|
|`-p` / `--process`|No|Flag to tell the script whether it should process all files in the source directory or only receently modified files.<br> The parameter supports two values - `all` or `modified`|
|`-m` / `--minutes`|No|Specify in minutes the time-limit for finding recently modified files. Can be used with `-p modified` option. <br> If this is not specified, the script will use a default value of `60` minutes.|


### Caveats
- In order to avoid processing wikilinks inside code blocks, the script will ignore lines beginning with 4 spaces. 
However, this means that a wikilink in a list that is on the 3rd level or deeper will not be converted. In other words:
```
- [[Level 1 wikilink]] # Will be converted
  - [[Level 2 wikilink]] # Will be converted
    - [[Level 3 wikilink]] # Will *NOT BE* converted
      - Any wikilinks in this level or deeper will also not be converted. 
```