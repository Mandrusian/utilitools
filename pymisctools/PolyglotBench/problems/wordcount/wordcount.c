#include <stdio.h>
#include <ctype.h>
int main(void) {
    int c, in_word = 0, count = 0;
    while ((c = getchar()) != EOF) {
        if (isspace(c)) in_word = 0;
        else if (!in_word) { in_word = 1; count++; }
    }
    printf("%d\n", count);
    return 0;
}
