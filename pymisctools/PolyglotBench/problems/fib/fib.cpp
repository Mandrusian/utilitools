#include <iostream>
int main() {
    long n; std::cin >> n;
    long a = 0, b = 1;
    for (long i = 0; i < n; i++) { long t = a; a = b; b = t + b; }
    std::cout << a << std::endl;
    return 0;
}
