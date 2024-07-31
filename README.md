# Calabash: a software energy experiments facilitator

Calabash automates the execution of comparative software level energy experiments. It uses Scaphandre under the hood, to sample Intel RAPL for power at the host and process level. 

## Design and Features

Calabash is comprised of two components: **Experiment** and **Analysis**. 

## Installation

## Usage

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