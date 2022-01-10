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

## Nice Stacktraces

```
adb logcat | nicelogcat --flat --stacktrace --disable
```

<img src="screenshots/5.png"/>

## All the colors of the Rainbow

<img src="screenshots/6.png"/>

## Filter

```
adb logcat | nicelogcat --flat "lines"
```

- Will filter any keys specified

<img src="screenshots/7.png"/>

- Restrictive filter with --all

```
adb logcat | nicelogcat --all --flat "lines" "Thread-6"
```

<img src="screenshots/8.png"/>


## Custom Titles per Line (if you want)!

```
adb logcat | nicelogcat --flat --show-title-every-line --title "Hello World"
```

<img src="screenshots/9.png"/>

## Dividers! Customizations!

```
adb logcat | nicelogcat --divider --linespace 4
```

<img src="screenshots/10.png"/>

## Log levels!

```
adb logcat | nicelogcat --flat --level ERROR
```

<img src="screenshots/11.png"/>

## More!

More hacks and surprises