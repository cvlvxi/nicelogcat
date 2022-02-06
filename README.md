# Nice 🪵 Log Cat 🐱

Just a dog pile of things that help pet the logcat

## Installing

```
cd [nicelogcat_directory]
pip install -r requirements.txt
pip install -e .
```

## Usage


See `nicelogcat --help` for usage

```
🎑  nicelogcat --help
Available keys:
        Show Configuration Key: f11
        Record Key: f12
usage: nicelogcatdebug [-h] [-f FILTER.INCLUDE] [--ftype {all,any}] [-x FILTER.EXCLUDE] [--xtype {all,any}] [-p FILTER.PREFIXES] [--ptype {all,any}]
                       [--pi FILTER.EXCLUDE_PREFIXES] [--pitype {all,any}] [--num-stacktrace STACKTRACE.NUM_STACK_TRACES]
                       [--num-lines-before-stacktrace STACKTRACE.PREV_LINES_BEFORE_STACKTRACE] [--stacktrace] [--h HIGHLIGHT.PHRASES] [--hp HIGHLIGHT.PREFIXES]
                       [-s LAYOUT.LINESPACE] [--rd RECORD.DIR] [--rk RECORD.KEYS] [--rf RECORD.FILENAME]

options:
  -h, --help            show this help message and exit
  -f FILTER.INCLUDE
  --ftype {all,any}
  -x FILTER.EXCLUDE
  --xtype {all,any}
  -p FILTER.PREFIXES
  --ptype {all,any}
  --pi FILTER.EXCLUDE_PREFIXES
  --pitype {all,any}
  --num-stacktrace STACKTRACE.NUM_STACK_TRACES
                        Num Stacktraces
  --num-lines-before-stacktrace STACKTRACE.PREV_LINES_BEFORE_STACKTRACE
                        Num Lines Before stacktrae
  --stacktrace          Enable Stacktrace
  --h HIGHLIGHT.PHRASES
                        Highlight these phrases
  --hp HIGHLIGHT.PREFIXES
                        Highlight these prefixes
  -s LAYOUT.LINESPACE   Spaces between log lines
  --rd RECORD.DIR       Directory to store recordings
  --rk RECORD.KEYS      Keys to record
  --rf RECORD.FILENAME  Filename to store recording under
```

# Basic Usage

```

adb logcat | nicelogcat

```