import os
from adblogs.colors import *
from collections import deque
from pathlib import Path

pause_logging = False

log_levels = {
    "I": ("INFO   ", Fg.green),
    "D": ("DEBUG  ", Fg.yellow),
    "W": ("WARN   ", Fg.yellow),
    "V": ("VERBOSE", Fg.yellow),
    "E": ("ERROR  ", Fg.red),
    "F": ("FATAL", Fg.red),
    "S": ("SILENT", Fg.white),

}

colors = {
    "process": Fg.green,
    "date": Fg.blue,
    "ip": Fg.red,
    "time": Fg.yellow,
    "current_time": Fg.magenta,
    "key": Fg.cyan,
    "subkey": Fg.red,
    "value": Fg.white,
    "boxmsg": Bg.yellow + Fg.black,
    "message": Fg.white,
    "submessage": Fg.yellow,
    "highlight": Bg.green + Fg.black,
    "highlight_prefix": Fg.green,
    "line_number": Fg.white,
}

MAX_LINE_BUFFER_SIZE = 1000 * 10

LINE_BUFFER = deque(maxlen=MAX_LINE_BUFFER_SIZE)

CURRENT_LINE_NUMBER = 0

ARGS_DELIM = ","

ZSH_HISTORY = Path(os.path.expanduser("~/.zsh_history"))

DEFAULT_TIME_LIMIT_SECS = 99999

# Defaults

DEFAULT_FIND = []

DEFAULT_VIVI_HIGHLIGHTS = [
    "box needs to be installed",
    "payload does not match schema"
]

DEFAULT_HIGHLIGHT_WORDS = [
    "clog"
] + DEFAULT_VIVI_HIGHLIGHTS

DEFAULT_FIND_IGNORE = [
    "getaddrinfo ENOTFOUND api.vivi.io",
    "at fail (/data/data/io.vivi.receiver/files/home/app/controller-proxy/controller-proxy.js:42:16)",
]

DEFAULT_EXCLUDE_KEYS = [
    "box_guid", 
    "mac_address", 
    "pid", 
    "level",
    "meta.box_guid",
    "meta.pid",
    "meta.mac_address",
    "meta.name"
]


DEFAULT_EXCLUDE_VALUES = [
    "INFO time",
    "sent via receptionist",
    "getTimeOk",
    "checking for zombie chromium instances to kill...",
    "use tinyAlsa",
    "getNetwork",
    "start process"
]

DEFAULT_VIVI_EXCLUDE_PREFIXES = [
    "ClockService",
    "FirewallController",
    "Firewall",
    "SchedulerService",
    "StreamOverlay",
    "StreamOverlayController",
    # "SignageController",
    "CommandUtil",
    "Unpacker",
    "FirewallController"
]

DEFAULT_EXCLUDE_PREFIXES = [
    "chatty",
    "DTVKIT_LOG",
    "HWComposer",
    "FASTGX_RC",
    "system_server",
    "storaged",
    "gralloc",
    "audio_hw_subMixingFactory",
    "audio-subMixingFactory",
    "MesonHwc",
    "amlaudioMixer",
    "dnsmasq",
    "Layer",
    "MediaBoxLauncher",
    "aml_audio_port",
    "libEGL",
    "Choreographer",
    "OpenGLRenderer",
    "DataProviderManager",
    "mali_winsys",
    "audio_hw_port",
    "dex2oat",
    "snmpd",
    "AlarmClock",
    "AlarmManagerService",
    "TelecomManager",
    "BtGatt.AdvertiseManager",
    "AVUtils",
    "audio_hw_primary",
    "OmxComponent",
    "GXFASTENCLIB",
    "OmxVideoEncoder",
    "AmlogicVideoAVCEncoder",
    "AshmemAllocator",
    "OMXNodeInstance",
    "OMX_WorkerPeer",
    "app_process",
    "GraphicBufferSource",
    "OMXUtils",
    "ACodec",
    "omx_core",
    "OmxResManage",
    "OmxLogConf",
    "OMXMaster",
    "OMXClient",
    "MtpDeviceJNI",
] + DEFAULT_VIVI_EXCLUDE_PREFIXES


BROKEN_MSGS = ["initial sync succeeded", "network sync succeeded", "sync: synced", "sync: live sync"]