#!/usr/bin/env python3

import time
from ctypes import *

lib = cdll.LoadLibrary("./build/zephyr/libzhci.so")

zhci_start_native = lib.zhci_start
zhci_test_native = lib.zhci_sc_test


def zhci_start(*args):
    argv = ["zhci".encode("utf-8")]
    for a in args:
        argv.append(a.encode("utf-8"))

    argv_c = (c_char_p * len(argv))()
    argv_c[:] = argv

    zhci_start_native(len(argv), argv_c)


zhci_start("--bt-dev=hci1")
zhci_test_native(42, 1337)
zhci_test_native(42, 1337)
zhci_test_native(42, 1337)
time.sleep(9999)
