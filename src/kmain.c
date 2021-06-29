#include <zephyr.h>
#include <pthread.h>
#include <string.h>
#include <init.h>
#include <malloc.h>

#ifndef NO_POSIX_CHEATS
#error "missing NO_POSIX_CHEATS"
#endif

int zhci_start(int argc, char **argv);
void zephyr_main(int argc, char **argv);

static pthread_cond_t cond_started = PTHREAD_COND_INITIALIZER;
static pthread_mutex_t mtx_started = PTHREAD_MUTEX_INITIALIZER;
static volatile bool started = false;

struct zephyr_main_args {
	int argc;
	char **argv;
};

static void *zephyr_main_thread(void *args_)
{
	const struct zephyr_main_args *args = args_;
	zephyr_main(args->argc, args->argv);

	return NULL;
}

int zhci_start(int argc, char **argv)
{
	int i;
	int ret;
	pthread_t thread;
	struct zephyr_main_args args = {
		.argc = 0,
		.argv = malloc(sizeof(*argv) * argc),
	};

	if (!args.argv) {
		return -ENOMEM;
	}

	for (i = 0; i < argc; i++) {
		args.argv[i] = strdup(argv[i]);
		if (!args.argv[i]) {
			ret = -ENOMEM;
			goto err_free_args;
		}
		args.argc++;
	}

	ret = pthread_create(&thread, NULL, zephyr_main_thread, &args);
	if (ret) {
		printk("can't create zephyr main thread: %d\n", ret);
		goto err_free_args;
	}

	pthread_mutex_lock(&mtx_started);
	while (!started) {
		pthread_cond_wait(&cond_started, &mtx_started);
	}
	pthread_mutex_unlock(&mtx_started);

	return 0;

err_free_args:
	for (i = 0; i < args.argc; i++) {
		free(args.argv[i]);
	}
	free(args.argv);
	return ret;
}

static int zhci_init(const struct device *dev)
{
	started = true;
	pthread_cond_broadcast(&cond_started);

	return 0;
}
SYS_INIT(zhci_init, POST_KERNEL, 0);
