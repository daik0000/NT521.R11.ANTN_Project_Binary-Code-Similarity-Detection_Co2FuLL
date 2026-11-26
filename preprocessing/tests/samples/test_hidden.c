/*
 * test_hidden.c — "Nhóm 2" sample: import hiding + string encryption.
 *
 * OLLVM fla/bcf/sub does not hide imports, so this sample simulates what
 * Hikari's function-call obfuscation / malware-style API hashing does:
 *   - every libc API used for the real work is resolved at run time with
 *     dlopen()/dlsym(); the names are XOR-encoded in the binary,
 *   - all user-visible strings are XOR-encoded and decoded on the fly.
 *
 * The static import table therefore only contains dlopen/dlsym (+ CRT
 * boilerplate), and `strings` shows none of the API names or messages.
 * Expected recovery (see tests/expected.json):
 *   imports : puts, malloc, free, strlen, memset, strcpy, snprintf
 *   strings : "Hello, hidden world!", "secret message decoded", ...
 */
#include <dlfcn.h>
#include <stddef.h>

#define KEY 0x5A

/* XOR-encoded with KEY, NUL terminator stored as KEY (decodes to 0). */
static unsigned char enc_libc[]     = {0x36,0x33,0x38,0x39,0x74,0x29,0x35,0x74,0x6c,0x5a};             /* libc.so.6 */
static unsigned char enc_puts[]     = {0x2a,0x2f,0x2e,0x29,0x5a};                                     /* puts */
static unsigned char enc_malloc[]   = {0x37,0x3b,0x36,0x36,0x35,0x39,0x5a};                           /* malloc */
static unsigned char enc_free[]     = {0x3c,0x28,0x3f,0x3f,0x5a};                                     /* free */
static unsigned char enc_strlen[]   = {0x29,0x2e,0x28,0x36,0x3f,0x34,0x5a};                           /* strlen */
static unsigned char enc_memset[]   = {0x37,0x3f,0x37,0x29,0x3f,0x2e,0x5a};                           /* memset */
static unsigned char enc_strcpy[]   = {0x29,0x2e,0x28,0x39,0x2a,0x23,0x5a};                           /* strcpy */
static unsigned char enc_snprintf[] = {0x29,0x34,0x2a,0x28,0x33,0x34,0x2e,0x3c,0x5a};                 /* snprintf */

/* "Hello, hidden world!" */
static unsigned char enc_msg1[] = {0x12,0x3f,0x36,0x36,0x35,0x76,0x7a,0x32,0x33,0x3e,0x3e,0x3f,0x34,
                                   0x7a,0x2d,0x35,0x28,0x36,0x3e,0x7b,0x5a};
/* "secret message decoded" */
static unsigned char enc_msg2[] = {0x29,0x3f,0x39,0x28,0x3f,0x2e,0x7a,0x37,0x3f,0x29,0x29,0x3b,0x3d,
                                   0x3f,0x7a,0x3e,0x3f,0x39,0x35,0x3e,0x3f,0x3e,0x5a};
/* "value=%d" */
static unsigned char enc_fmt[]  = {0x2c,0x3b,0x36,0x2f,0x3f,0x67,0x7f,0x3e,0x5a};

typedef int    (*puts_t)(const char *);
typedef void  *(*malloc_t)(size_t);
typedef void   (*free_t)(void *);
typedef size_t (*strlen_t)(const char *);
typedef void  *(*memset_t)(void *, int, size_t);
typedef char  *(*strcpy_t)(char *, const char *);
typedef int    (*snprintf_t)(char *, size_t, const char *, ...);

static puts_t     p_puts;
static malloc_t   p_malloc;
static free_t     p_free;
static strlen_t   p_strlen;
static memset_t   p_memset;
static strcpy_t   p_strcpy;
static snprintf_t p_snprintf;

static void decode(unsigned char *s) {
    for (; *s != KEY; s++)
        *s ^= KEY;
    *s = 0;
}

static void *resolve(void *lib, unsigned char *enc_name) {
    decode(enc_name);
    return dlsym(lib, (const char *)enc_name);
}

static int resolve_all(void) {
    decode(enc_libc);
    void *lib = dlopen((const char *)enc_libc, RTLD_NOW);
    if (!lib)
        return -1;
    p_puts     = (puts_t)resolve(lib, enc_puts);
    p_malloc   = (malloc_t)resolve(lib, enc_malloc);
    p_free     = (free_t)resolve(lib, enc_free);
    p_strlen   = (strlen_t)resolve(lib, enc_strlen);
    p_memset   = (memset_t)resolve(lib, enc_memset);
    p_strcpy   = (strcpy_t)resolve(lib, enc_strcpy);
    p_snprintf = (snprintf_t)resolve(lib, enc_snprintf);
    return 0;
}

static char *copy_secret(void) {
    decode(enc_msg2);
    size_t n = p_strlen((const char *)enc_msg2);
    char *buf = (char *)p_malloc(n + 1);
    p_memset(buf, 0, n + 1);
    p_strcpy(buf, (const char *)enc_msg2);
    return buf;
}

int main(void) {
    if (resolve_all() != 0)
        return 1;
    decode(enc_msg1);
    p_puts((const char *)enc_msg1);

    char *secret = copy_secret();
    p_puts(secret);

    char line[32];
    decode(enc_fmt);
    p_snprintf(line, sizeof(line), (const char *)enc_fmt, 42);
    p_puts(line);

    p_free(secret);
    return 0;
}
