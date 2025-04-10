#include <stdio.h>
#include <stdlib.h>
#define __USE_GNU
#include <pthread.h>
#include <x86intrin.h>
#include <sched.h>
#include <stdint.h>
#include <math.h>
#include <unistd.h>
#include <sys/time.h>

#define FLOAT 0
#define BRANCH 0

#define P_FREQ 4800000
#define E_FREQ 3600000

#define LOG_TUNE_TIME 0

#define CORES 20
#define THREADS 12

int p_loop_calibration = 3000;
int e_loop_calibration = 1500;

typedef struct
{
    int core_num;
} args;

pthread_t t[THREADS];
args t_arg[THREADS];
args t_arg_sec[THREADS];

void attach_core(int cpu)
{
    cpu_set_t mask;
    cpu_set_t get;
    int num = 20;
    CPU_ZERO(&mask);

    CPU_SET(cpu, &mask);
    sched_setaffinity(0, sizeof(mask), &mask);

}

static inline uint64_t rdtscp()
{
    uint64_t rax, rdx;
    asm volatile("rdtscp\n"
                 : "=a"(rax), "=d"(rdx)::"%rcx", "memory");
    return (rdx << 32) | rax;
}

void *e_worker(void *thread_args)
{
    args param = *(args *)thread_args;
    attach_core(param.core_num);

    int i, j;
    _mm_lfence();

    unsigned long a = 1121, b = 562, c1 = 3233, c2 = 7879, d = 42345;
    unsigned long e = 5234, g = 2347, f = 245, h;
    float ftemp = 6.3, fcoca = 3.2, fpepsi = 777.1;

    for(i = 0; i < p_loop_calibration; i++)
    {
        h = rand() % 10;
        __asm__ __volatile__ (
            "movq %0, %%r8\n\t"
            "adcq $4234, %%r8\n\t"

            "movq %1, %%r9\n\t"
            "sbbq $212, %%r9\n\t"

            "movq %2, %%r12\n\t"
            "mov $6, %%cl\n\t"
            "shld %%cl, %%r12, %%rax\n\t"

            "movq %4, %%r10\n\t"
            "andq $0x7F, %%r10\n\t"
        #if BRANCH == 1
            "cmpq $0x7, %8\n\t"
            "jg greater\n\t"
            "jmp less\n\t"
            "greater:\n\t"
        #endif
            "movq %5, %%rsi\n\t"
            "btcq $15, %%rsi\n\t"

            "movq %6, %%rdi\n\t"
            "orq $0xACBD, %%rdi\n\t"

            "movq %7, %%r11\n\t"
            "xorq $0x157D, %%r11\n\t"
        #if BRANCH == 1
            "less:\n\t"
        #endif
            :
            : "r" (a), "r" (b), "r" (c1), "r" (c2), "r" (d), "r" (e), "r" (f), "r" (g), "r" (h)
            :
            // : "%rax", "%rsi", "%cl", "%rdi", "%r8", "%r9", "%r10", "%r11", "%r12"
            // : "%rax", "%rbx", "%rcx", "%rdx", "%rsi", "%rdi", "%r8", "%r9", "%r10", "%r11"
        );
    }
}

void *p_worker(void *thread_args)
{
    args param = *(args *)thread_args;
    // attach_core(param.core_num);

    int i, j;
    _mm_lfence();

    unsigned long a = 1121, b = 562, c1 = 3233, c2 = 7879, d = 42345;
    unsigned long e = 5234, g = 2347, f = 245, h;
    float ftemp = 6.3, fcoca = 3.2, fpepsi = 777.1;

    for(i = 0; i < e_loop_calibration; i++)
    {
        h = rand() % 10;
        __asm__ __volatile__ (
            "movq %0, %%r8\n\t"
            "adcq $4234, %%r8\n\t"

            "movq %1, %%r9\n\t"
            "sbbq $212, %%r9\n\t"

            "movq %2, %%r12\n\t"
            "mov $6, %%cl\n\t"
            "shld %%cl, %%r12, %%rax\n\t"

            "movq %4, %%r10\n\t"
            "andq $0x7F, %%r10\n\t"
        #if BRANCH == 1
            "cmpq $0x7, %8\n\t"
            "jg greater\n\t"
            "jmp less\n\t"
            "greater:\n\t"
        #endif
            "movq %5, %%rsi\n\t"
            "btcq $15, %%rsi\n\t"

            "movq %6, %%rdi\n\t"
            "orq $0xACBD, %%rdi\n\t"

            "movq %7, %%r11\n\t"
            "xorq $0x157D, %%r11\n\t"
        #if BRANCH == 1
            "less:\n\t"
        #endif
            :
            : "r" (a), "r" (b), "r" (c1), "r" (c2), "r" (d), "r" (e), "r" (f), "r" (g), "r" (h)
            :
            // : "%rax", "%rsi", "%cl", "%rdi", "%r8", "%r9", "%r10", "%r11", "%r12"
            // : "%rax", "%rbx", "%rcx", "%rdx", "%rsi", "%rdi", "%r8", "%r9", "%r10", "%r11"
        );
    }
}

void sender(int p_e)
{
    int i = 0;
    if(p_e - 1 == 0)        // P core worker.
    {
        for(i = 0; i < THREADS - 4; i++){
            pthread_create(&t[i], NULL, p_worker, (void *)&t_arg[i]);
        }
        for (i = 0; i < THREADS - 4; i++)
        {
            pthread_join(t[i], NULL);
        }
    }
    else
    {
        for(i = THREADS - 4; i < THREADS; i++){
            pthread_create(&t[i], NULL, e_worker, (void *)&t_arg[i]);
        }
        for (i = THREADS - 4; i < THREADS; i++)
        {
            pthread_join(t[i], NULL);
        }
    }
}

void test_latency()
{
    int p_e = 0;
    printf("latency test: P or E?\n");
    for(int j = 0; j < 10; j++)
    {
        for(int i = 0; i < 10; i++)
        {
            sender(1);
            printf("P running\n");
        }
        for(int i = 0; i < 10; i++)
        {
            sender(2);
            printf("E running\n");
        }
    }
}

void calibration(){
    uint64_t st, used;
    int send_seq[10] = {1, 1, 1, 1, 1, 2, 2, 2, 2, 2};
    for(int i = 0; i < 10; i++)
    {
        st = rdtscp();
        sender(send_seq[i]);
        used = rdtscp() - st;
        if(send_seq[i] == 1){
            printf("P running time: %lf ms\n", used * 1.0 / P_FREQ);
        }
        else
            printf("E running time: %lf ms\n", used * 1.0 / E_FREQ);
    }
}

int main(int argc, char *argv[])
{
    int i, j;
    uint64_t st, used;

    for (i = 0; i < THREADS - 4; i++)
    {
        t_arg[i].core_num = i * 2;
    }
    for(i = 0; i < 4; i++)
    {
        t_arg[i + THREADS - 4].core_num = 16 + i;
    }


    calibration();
    
    int cali_flag = 0;
    printf("Calibrate?\n");
    scanf("%d", &cali_flag);
    while(cali_flag){
        printf("input P / E loop, now: %d, %d\n", p_loop_calibration, e_loop_calibration);
        scanf("%d %d", &p_loop_calibration, &e_loop_calibration);
        calibration();
        printf("Need calibrate?\n");
        scanf("%d", &cali_flag);
    }

    FILE *fp = fopen(argv[1], "rb");
    printf("The bits-file name: %s\n", argv[1]);
    char buffer[2048] = "";
    size_t bytes_read = fread(buffer, sizeof(char), sizeof(buffer), fp);
    printf("len of send bits: %lu\n", bytes_read);
    fclose(fp);
    printf("The bits to be send:\n");
    for(i = 0; i < bytes_read/8; i++){
        for(j = 0; j < 8; j++)
        {
            printf("%c", buffer[i * 8 + j]);
        }
    }
    printf("\n");
    fflush(stdout);
    
    // We need to get the status shift sequences.
    int on_off = 0;     // 0 means now we want P running 
    int shift_seq[2048] = {0};
    printf("The running sequence: (0 -> P, 1 -> E)\n");
    for(i = 0; i < bytes_read; i++)
    {
        if(buffer[i] == '0')    // Indicate keep running on the same switch
        {
            shift_seq[i] = on_off + 1;       // We use 1 and 2 to represent P and E running.
        }
        else
        {
            on_off = (on_off + 1) % 2;
            shift_seq[i] = on_off + 1;
        }
        printf("%d", shift_seq[i] - 1);
    }


    printf("\nGetchar then start\n");
    getchar();
    getchar();
    printf("Start sending.\n%ld\n", rdtscp());

    for(i = 0; i < bytes_read - 1; i++)
    {
    #if LOG_TUNE_TIME == 1
        st = rdtscp();
    #endif
        sender(shift_seq[i]);
    #if LOG_TUNE_TIME == 1
        used = rdtscp() - st;
        if(shift_seq[i] == 1){
            printf("P running time: %lf ms\n", used * 1.0 / P_FREQ);
        }
        else
            printf("E running time: %lf ms\n", used * 1.0 / E_FREQ);
    #endif
    }
    printf("End sending.\n%ld\n", rdtscp());
    return 0;
}
