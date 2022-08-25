import subprocess


def adb_clear():
    print("Clearing logcat!")
    subprocess.call(["adb", "logcat", "-c"])


def adb_logs(ip=None):
    while True:
        logcat_cmd = ["adb", "logcat"]
        if ip:
            logcat_cmd = ["adb", "-s", f"{ip}:5555", "logcat"]
        ps = subprocess.Popen(logcat_cmd, stdout=subprocess.PIPE, stdin=subprocess.PIPE)
        while True:
            line = ps.stdout.readline().decode().strip()
            if not line:
                break
            yield line
        print("Restarting adb")
        ps.kill()

