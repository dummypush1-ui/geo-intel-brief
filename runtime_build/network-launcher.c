/* Candidate build-input source, not runtime/ABI/512MB acceptance proof. */
#define _GNU_SOURCE
#include <errno.h>
#include <linux/audit.h>
#include <linux/filter.h>
#include <linux/seccomp.h>
#include <stddef.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/prctl.h>
#include <sys/syscall.h>
#include <unistd.h>
#define DENY(n) BPF_JUMP(BPF_JMP|BPF_JEQ|BPF_K,(n),0,1), BPF_STMT(BPF_RET|BPF_K,SECCOMP_RET_ERRNO|EPERM)
int main(int argc,char **argv) {
    if (argc < 2 || strcmp(argv[1],"/opt/runtime27b/bin/python") != 0) {
        fputs("Only fixed candidate Python executable allowed\n",stderr);return 64;
    }
    /* Fail closed on inherited nonstdio descriptors; close_range needs real target test. */
    if (syscall(SYS_close_range,3u,~0u,0u)!=0) {perror("close_range");return 70;}
    struct sock_filter filter[]={
        BPF_STMT(BPF_LD|BPF_W|BPF_ABS,offsetof(struct seccomp_data,arch)),
        BPF_JUMP(BPF_JMP|BPF_JEQ|BPF_K,AUDIT_ARCH_X86_64,1,0),
        BPF_STMT(BPF_RET|BPF_K,SECCOMP_RET_KILL_PROCESS),
        BPF_STMT(BPF_LD|BPF_W|BPF_ABS,offsetof(struct seccomp_data,nr)),
        /* Reject x32 ABI syscall-number bypass. */
        BPF_JUMP(BPF_JMP|BPF_JGE|BPF_K,0x40000000u,0,1),
        BPF_STMT(BPF_RET|BPF_K,SECCOMP_RET_KILL_PROCESS),
        DENY(SYS_socket),DENY(SYS_socketpair),DENY(SYS_connect),
        DENY(SYS_bind),DENY(SYS_listen),DENY(SYS_accept),DENY(SYS_accept4),
        DENY(SYS_sendto),DENY(SYS_sendmsg),DENY(SYS_sendmmsg),
        DENY(SYS_recvfrom),DENY(SYS_recvmsg),DENY(SYS_recvmmsg),
        /* io_uring can otherwise submit network operations. */
        DENY(SYS_io_uring_setup),DENY(SYS_io_uring_enter),DENY(SYS_io_uring_register),
        BPF_STMT(BPF_RET|BPF_K,SECCOMP_RET_ALLOW)
    };
    struct sock_fprog program={.len=(unsigned short)(sizeof(filter)/sizeof(filter[0])),.filter=filter};
    if(prctl(PR_SET_NO_NEW_PRIVS,1,0,0,0)!=0) {perror("no_new_privs");return 70;}
    if(prctl(PR_SET_SECCOMP,SECCOMP_MODE_FILTER,&program)!=0) {perror("seccomp");return 70;}
    execv(argv[1],argv+1);perror("execv");return 70;
}
