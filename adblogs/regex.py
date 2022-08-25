import re


r_space = r"\s*"
r_date = r"(?P<date>\d\d-\d\d)"
r_time = r"(?P<time>\d\d:\d\d:\d\d.\d\d\d)"
r_pid = r"(\d+)"
r_level = r"(?P<level>.)"
# This needs to be greedy
r_prefix = r"(?P<prefix>.*?\s*:)"
r_message = r"(?P<message>.*)"
# Get last occurance
r_json = r"(?P<pre_json>.*)(?P<json>^\{.*\}$)(?P<post_json>.*)"


line_regex_parts = [r_date, r_time, r_pid, r_pid, r_level, r_prefix, r_message]
line_regex = r_space.join(line_regex_parts)
line_regex = re.compile(r_space.join(line_regex_parts))
json_regex = re.compile(r_json)


# meta
r_meta_line = r".*\"meta\":.*(?P<level>INFO|DEBUG|WARN|ERROR) (?P<name>.*): (?P<message>.*) (?P<json>\{.*)$"
meta_regex = re.compile(r_meta_line)