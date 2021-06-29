# SPDX-License-Identifier: Apache-2.0

cmake_minimum_required(VERSION 3.13.1)

find_package(Zephyr REQUIRED HINTS $ENV{ZEPHYR_BASE})
project(hello_world)

set(zhci_syscalls_h ${CMAKE_CURRENT_LIST_DIR}/include/zhci_syscalls.h)
set(generated_zhci_syscalls_h ${CMAKE_CURRENT_BINARY_DIR}/generated/include/generated/_zhci_syscalls.h)
set(generated_zhci_syscalls_c ${CMAKE_CURRENT_BINARY_DIR}/generated/src/zhci_syscalls.c)

add_custom_command(
    OUTPUT
    ${generated_zhci_syscalls_h}
    ${generated_zhci_syscalls_c}
    COMMAND
    ${PYTHON_EXECUTABLE} ${CMAKE_CURRENT_LIST_DIR}/scripts/parse_syscalls.py
        --include ${CMAKE_CURRENT_LIST_DIR}/include/zhci_syscalls.h
        --header-file ${generated_zhci_syscalls_h}
        --source-file ${generated_zhci_syscalls_c}
    DEPENDS
    ${zhci_syscalls_h}
    ${CMAKE_CURRENT_LIST_DIR}/scripts/parse_syscalls.py
)
add_custom_target(zhci_syscalls DEPENDS
    ${generated_zhci_syscalls_h}
    ${generated_zhci_syscalls_c}
)

set_source_files_properties(src/kmain.c PROPERTIES COMPILE_FLAGS -DNO_POSIX_CHEATS)
set_source_files_properties(src/offload.c PROPERTIES COMPILE_FLAGS -DNO_POSIX_CHEATS)

target_sources(app PRIVATE
    ${generated_zhci_syscalls_c}
    src/kmain.c
    src/offload.c
    src/main.c
)
target_include_directories(app PRIVATE
    ${CMAKE_CURRENT_LIST_DIR}/include
    ${CMAKE_CURRENT_BINARY_DIR}/generated/include
)
target_compile_options(app PRIVATE
    -Wmissing-prototypes
)
add_dependencies(app zhci_syscalls)
