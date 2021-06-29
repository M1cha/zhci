#include <zephyr.h>
#include <pthread.h>
#include <zhci_syscalls.h>
#include <irq_ctrl.h>
#include <app_offload.h>

#ifndef NO_POSIX_CHEATS
#error "missing NO_POSIX_CHEATS"
#endif

#define OFFLOAD_HW_IRQ 10

static void (*off_hw_routine)(void *);
static void *off_hw_parameter;
static pthread_mutex_t off_hw_mtx = PTHREAD_MUTEX_INITIALIZER;
static pthread_cond_t off_hw_cond = PTHREAD_COND_INITIALIZER;
static pthread_mutex_t off_hw_condmtx = PTHREAD_MUTEX_INITIALIZER;

K_SEM_DEFINE(off_hw_sem, 0, 1);

static void offload_hw_irq_handler(const void *a)
{
	ARG_UNUSED(a);
	k_sem_give(&off_hw_sem);
}

void posix_irq_offload_hw(void (*routine)(void *), void *parameter)
{
	pthread_mutex_lock(&off_hw_mtx);
	pthread_mutex_lock(&off_hw_condmtx);

	off_hw_routine = routine;
	off_hw_parameter = parameter;

	posix_isr_declare(OFFLOAD_HW_IRQ, 0, offload_hw_irq_handler, NULL);
	posix_irq_enable(OFFLOAD_HW_IRQ);
	hw_irq_ctrl_raise_im(OFFLOAD_HW_IRQ);
	posix_irq_disable(OFFLOAD_HW_IRQ);

	while (off_hw_routine) {
		pthread_cond_wait(&off_hw_cond, &off_hw_condmtx);
	}

	pthread_mutex_unlock(&off_hw_condmtx);
	pthread_mutex_unlock(&off_hw_mtx);
}

void app_offload_handle(void)
{
	for (;;) {
		k_sem_take(&off_hw_sem, K_FOREVER);

		if (off_hw_routine) {
			off_hw_routine(off_hw_parameter);

			off_hw_routine = NULL;
			off_hw_parameter = NULL;
			pthread_cond_broadcast(&off_hw_cond);
		}
	}
}
