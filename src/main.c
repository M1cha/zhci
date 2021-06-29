#include <zephyr.h>
#include <sys/printk.h>
#include <zhci_syscalls.h>
#include <app_offload.h>

void main(void)
{
	printk("Hello World! %s\n", CONFIG_BOARD);

	app_offload_handle();
}

int zhci_sc_test_impl(int a, int b) {
    printk("hello from main thread a=%d b=%d\n", a, b);
    return 0;
}
