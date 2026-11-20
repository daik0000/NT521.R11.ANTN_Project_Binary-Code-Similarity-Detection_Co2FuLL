/*
 * test_subject.c — subject program for the stage-0 preprocessing tests.
 *
 * Based on section 8.1 of preprocessing_pipeline_design.md. Kept small but
 * with enough imports, meaningful string literals and branching logic so
 * that CFF/BCF obfuscation has something to flatten.
 *
 * Note: the design's example reads tmp[0] after free() (use-after-free);
 * here the result is copied before freeing.
 */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

void greet(const char *name) {
    char buf[64];
    snprintf(buf, sizeof(buf), "Hello, %s!", name);
    printf("%s\n", buf);
}

int compute(int x, int y) {
    int *tmp = (int *)malloc(sizeof(int) * 2);
    int result;
    tmp[0] = x + y;
    tmp[1] = x * y;
    printf("sum=%d, product=%d\n", tmp[0], tmp[1]);
    result = tmp[0];
    free(tmp);
    return result;
}

int classify(int value) {
    int score = 0;
    if (value < 0) {
        puts("classify: negative value");
        score = -1;
    } else if (value % 2 == 0) {
        puts("classify: even value");
        score = value / 2;
    } else {
        puts("classify: odd value");
        score = value * 3 + 1;
    }
    for (int i = 0; i < value && i < 8; i++) {
        score += i;
    }
    return score;
}

char *duplicate_message(const char *msg) {
    size_t len = strlen(msg);
    char *copy = (char *)malloc(len + 1);
    memset(copy, 0, len + 1);
    strcpy(copy, msg);
    return copy;
}

int main(int argc, char *argv[]) {
    (void)argv;
    greet("BinKit");
    int r = compute(6, 7);
    int c = classify(r + argc);
    char *m = duplicate_message("binary code similarity detection");
    printf("result=%d class=%d msg=%s\n", r, c, m);
    free(m);
    return 0;
}
