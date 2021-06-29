#ifndef APP_OFFLOAD_H
#define APP_OFFLOAD_H

void posix_irq_offload_hw(void (*routine)(void *), void *parameter);
void app_offload_handle(void);

#endif /* APP_OFFLOAD_H */
