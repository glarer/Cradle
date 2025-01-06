#define __USE_GNU
#include <stdio.h>
#include <stdint.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>
#include <unistd.h>
#include <sys/mman.h>

#ifndef MAP_HUGE_1GB
#define MAP_HUGE_1GB (30 << MAP_HUGE_SHIFT)
#endif

// Modify the RECORD_NUM to change the number of sampling.
#define RECORD_NUM 50000 

static inline uint64_t rdtscp()
{
    uint64_t rax, rdx;
    asm volatile("rdtscp\n"
                 : "=a"(rax), "=d"(rdx)::"%rcx", "memory");
    return (rdx << 32) | rax;
}

int main(int argc, char *argv[])
{
    uint64_t len = RECORD_NUM*sizeof(uint64_t);
    uint64_t *time_stamp = (uint64_t *)mmap(NULL, len, PROT_READ | PROT_WRITE, MAP_ANONYMOUS | MAP_PRIVATE | MAP_HUGETLB | MAP_HUGE_1GB, -1, 0);
    if (time_stamp == (void *)(-1))
    {
        perror("ERROR: mmap of array a failed! ");
        exit(1);
    }

    memset((void *)time_stamp, '\x00', RECORD_NUM*sizeof(uint64_t));
    for(int i = 0; i < RECORD_NUM; i++)
    {
        time_stamp[i] = 0;
    }

    uint64_t i = 0, j = 0;
    uint64_t cur_cyc = 0;

    double ms = atof(argv[1]);
    printf("ms: %lf\n", ms);
    struct timespec req, rem;
    req.tv_sec = 0;
    req.tv_nsec = (long long)(1000000 * ms);    // convert from ms (for sleep)
    // ! The resolution is 1000ns -> 1 us -> 0.001 ms
    uint64_t time_n = rdtscp();
    for(i = 0; i < RECORD_NUM; i++)
    {
        time_n = rdtscp();
        time_stamp[i] = time_n;
        nanosleep(&req, &rem);
    }

    FILE *fp = fopen("./logs/time_stamp.txt", "w");
    fwrite(time_stamp, sizeof(uint64_t), RECORD_NUM, fp);

    fclose(fp);
    munmap((void *)time_stamp, len);
    return 0;
}