#include <stdio.h>
int main(void) {
    long n; if (scanf("%ld", &n) != 1) return 1;
    long a = 0, b = 1;
    for (long i = 0; i < n; i++) { long t = a; a = b; b = t + b; }
    printf("%ld\n", a);
    return 0;
}
