# Calabash: a software energy experiments facilitator

Calabash automates the execution of comparative software level energy experiments. It uses Scaphandre under the hood, to sample Intel RAPL for power at the host and process level. 

## Design and Features

Calabash is comprised of two components: **Experiment** and **Analysis**. 

## Installation
### Requirements
If using the experimenter module, the following requirements must be met:
- Must be on Linux, preferably with Ubuntu 22.04
- Docker
- Intel processor

### Install using pip
The easiest way to use Calabash is by using `pip install calabash-experimenter`

### Use Calabash through the source code
You may also choose to clone the git repository and run the main function directly. Before doing this install are requirements with `pip install -r requirements.txt` from the root directory.

Then use add the desired command to the end of `$python src/main.py <command>`

## Usage
Before using Calabash, you must create a configuration file according to the specification below.

### Configuration YAML
```
images:
 - "<dockerhub image name>"
 - ...
out: "<path to directory for output>"
procedure:
  internal_repetitions: <number of repititons within the application (passed into the container)>
  external_repetitions: <number of repititions of the entire image>
  freq: <sampling frequency in nanoseconds>
  cooldown: <seconds in between image runs>
analysis:
    mode: <regex | pid>
    regex: "<regular expression to match on if regex mode is specified>"
```

With the configuration file you can use the `experiment <config_path>` or `analyze <config_path>` to run either module. Note that for proper analysis, the same configuration file should be provided for both. 