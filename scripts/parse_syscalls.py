#!/usr/bin/env python3
#
# Copyright (c) 2017 Intel Corporation
#
# SPDX-License-Identifier: Apache-2.0

"""
Script to scan Zephyr include directories and emit system call and subsystem metadata

System calls require a great deal of boilerplate code in order to implement
completely. This script is the first step in the build system's process of
auto-generating this code by doing a text scan of directories containing
C or header files, and building up a database of system calls and their
function call prototypes. This information is emitted to a generated
JSON file for further processing.

This script also scans for struct definitions such as __subsystem and
__net_socket, emitting a JSON dictionary mapping tags to all the struct
declarations found that were tagged with them.

If the output JSON file already exists, its contents are checked against
what information this script would have outputted; if the result is that the
file would be unchanged, it is not modified to prevent unnecessary
incremental builds.
"""

import argparse
import json
import os
import re
import sys

regex_flags = re.MULTILINE | re.VERBOSE

syscall_regex = re.compile(
    r"""
__zhci_syscall\s+                    # __syscall attribute, must be first
([^(]+)                         # type and name of system call (split later)
[(]                             # Function opening parenthesis
([^)]*)                         # Arg list (split later)
[)]                             # Closing parenthesis
""",
    regex_flags,
)

typename_regex = re.compile(r"(.*?)([A-Za-z0-9_]+)$")


class SyscallParseException(Exception):
    pass


def typename_split(item):
    if "[" in item:
        raise SyscallParseException(
            "Please pass arrays to syscalls as pointers, unable to process '%s'" % item
        )

    if "(" in item:
        raise SyscallParseException("Please use typedefs for function pointers")

    mo = typename_regex.match(item)
    if not mo:
        raise SyscallParseException("Malformed system call invocation")

    m = mo.groups()
    return (m[0].strip(), m[1])


def analyze_fn(match_group):
    func, args = match_group

    try:
        if args == "void":
            args = []
        else:
            args = [typename_split(a.strip()) for a in args.split(",")]

        func_type, func_name = typename_split(func)
    except SyscallParseException:
        sys.stderr.write("In declaration of %s\n" % func)
        raise

    return (func_type, func_name, args)


def analyze_headers(h, c, path):
    with open(path, "r", encoding="utf-8") as fp:
        contents = fp.read()

    syscalls = [mo.groups() for mo in syscall_regex.finditer(contents)]

    c.write("#include <zhci_syscalls.h>\n\n")
    c.write("#include <app_offload.h>\n\n")

    h.write("#ifndef GENERATED_ZHCI_SYSCALLS_H\n")
    h.write("#define GENERATED_ZHCI_SYSCALLS_H\n\n")
    h.write("#define __zhci_syscall\n\n")

    for match_group in syscalls:
        func_type, func_name, args = analyze_fn(match_group)

        h.write(f"{func_type} {func_name}_impl({match_group[1]});\n")

        # argument struct
        c.write(f"struct zhci_args_{func_name} {{\n")
        if func_type != "void":
            c.write(f"    {func_type} r;\n")
        for index, (arg_type, arg_name) in enumerate(args):
            c.write(f"    {arg_type} a{index};\n")
        c.write(f"}};\n\n")

        # wrapper symbol
        c.write(f"static void zhci_wrapper_{func_name}(void *args_) {{\n")
        c.write(f"    struct zhci_args_{func_name} *args = args_;\n")
        impl_args = ["args->a" + str(i) for i in range(len(args))]
        impl_ret = "args->r = " if func_type != "void" else ""
        c.write(f"    {impl_ret}{func_name}_impl({', '.join(impl_args)});\n")
        c.write(f"}}\n\n")

        # public symbol
        c.write(f"{func_type} {func_name}({match_group[1]}) {{\n")
        c.write(f"    struct zhci_args_{func_name} args = {{\n")
        for index, (arg_type, arg_name) in enumerate(args):
            c.write(f"        .a{index} = {arg_name},\n")
        c.write(f"    }};\n")
        c.write(f"    posix_irq_offload_hw(zhci_wrapper_{func_name}, &args);\n")
        if func_type != "void":
            c.write(f"    return args.r;\n")
        c.write(f"}}\n\n\n")

    h.write("\n#endif /* GENERATED_ZHCI_SYSCALLS_H */\n")


def parse_args():
    global args
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )

    parser.add_argument(
        "-i",
        "--include",
        required=True,
    )
    parser.add_argument(
        "--source-file",
        required=True,
    )
    parser.add_argument(
        "--header-file",
        required=True,
    )
    args = parser.parse_args()


def main():
    parse_args()

    with open(args.header_file, "w") as h:
        with open(args.source_file, "w") as c:
            analyze_headers(h, c, args.include)


if __name__ == "__main__":
    main()
