from constants import *
from colorama import Style, Fore, Back


def norm_str(some_str):
    some_str = some_str.strip()
    some_str = some_str.replace('"', "")
    some_str = some_str.replace("'", "")
    some_str = some_str.replace("\\", "")
    return some_str


def norm_str2(some_str):
    some_str = some_str.replace("\\n", "\n")
    some_str = some_str.replace("\\", "")
    some_str = some_str.replace('""', '"')
    some_str = some_str.replace("''", "'")
    some_str = some_str.replace('":"', '": "')
    return some_str


def norm_str3(some_str):
    some_str = some_str.strip()
    if not some_str:
        return ""
    bad_chars = ":\\/\\'\""
    if some_str[0] in bad_chars:
        some_str = some_str[1:]
    if len(some_str) > 1 and some_str[-1] in bad_chars:
        some_str = some_str[0:-1]
    return some_str


def remove_col_from_val(val):
    new_val = val
    for col in ALL_COLORS:
        if col in val:
            new_val = new_val.replace(col, "")
    return new_val


def style(val, min_len=None, color=None):
    if not val or not isinstance(val, str):
        return val
    new_val = remove_col_from_val(val)
    new_val_len = len(new_val)
    spacer = " "
    if min_len:
        if new_val_len < min_len:
            new_val = val + spacer * (min_len - new_val_len)
        else:
            raise ValueError(
                "orig_val: {} new_val: {} has length: {} which is bigger than {}".format(
                    val, new_val, new_val_len, min_len
                )
            )
    if color:
        val = color + val + Style.RESET_ALL
    return val


def nested_dicts(some_dict, level=0):
    new_dict = {}
    for k, v in some_dict.items():
        value = None
        try:
            value = json.loads(v)
        except:
            value = v
        if not isinstance(value, dict):
            new_dict[k] = v
            continue
        for subk, subv in value.items():
            if isinstance(subv, dict):
                new_dict[subk] = nested_dicts(subv, level=level + 1)
            else:
                if subk in new_dict.keys():
                    continue
                    # subk = f"{subk}_{level}"
                new_dict[subk] = subv
    return new_dict


def find_dict_in_v(v, rawline=None):
    if "{" in v and "}" in v:
        first_bracket_idx = v.find("{")
        last_bracket_idx = v.rfind("}")
        json_str = v[first_bracket_idx : last_bracket_idx + 1]
        try:
            val = json.loads(json_str)
            return val
        except Exception as e:
            return {}

    else:
        return {}
