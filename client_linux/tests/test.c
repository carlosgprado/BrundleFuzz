// Compile with:
// gcc -fno-stack-protector -o test test.c
//

#include <stdio.h>
#include <string.h>
#include <stdlib.h>
#include <fcntl.h>
#include <errno.h>
#include <sys/types.h>
#include <unistd.h>

#define BUF_SIZE 8192

void boom(char* s)
{
    char buf[64] = {0};
    // BOOM!
    strcpy(buf, s);
}

int main(int argc, char *argv[])
{
    int fd;
    ssize_t ret;
    char buffer[BUF_SIZE] = {0};

    fd = open(argv[1], O_RDONLY);
    if(fd == -1) {
        perror("open");
        return 1;
    }

    ret = read(fd, &buffer, BUF_SIZE);
    if(buffer[0] == 'A') {
        if(buffer[2] == 'X') {
            boom(buffer);
        }
    }    
    
    return 0;
}
