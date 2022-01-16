import pytest
from nicelogcat.logcat import main_loop


def test_prefix(args_prefix, logstream):
    logs = [x for x in (
        main_loop(args=args_prefix, stream=logstream))]
    assert len(logs) == 1


def test_title(args_title, logstream):
    logs = [x for x in (
        main_loop(args=args_title, stream=logstream))]
    assert "hello" in logs[0]

def test_filter_all(args_filter_all, logstream):
    logs = [x for x in (
        main_loop(args=args_filter_all, stream=logstream))]
    assert len(logs) == 3

def test_filter_any(args_filter_any, logstream):
    logs = [x for x in (
        main_loop(args=args_filter_any, stream=logstream))]
    assert len(logs) == 5