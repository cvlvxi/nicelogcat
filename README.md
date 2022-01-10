# Nice Log Cat

Just a dog pile of things that help pet the logcat

## Installing

```
pip install -e .
```

## Usage


See `nicelogcat --help` for usage

## Simple

```
adb logcat | nicelogcat --flat
```

<img src="screenshots/1.png"/>

## Filter by prefix

```
adb logcat | nicelogcat --flat -p tvos
```


<img src="screenshots/2.png"/>

## Record

Hit f12 while nicelogcatting to start and stop recording and write to a log file


<img src="screenshots/3.png"/>

## Record only when keys change

```
adb logcat | nicelogcat -p Logger --flat --record-keys x
```
<img src="screenshots/4.png"/>

## More!

More hacks and surprises 