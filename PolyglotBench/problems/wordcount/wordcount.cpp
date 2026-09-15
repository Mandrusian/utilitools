#include <iostream>
#include <sstream>
#include <string>
int main() {
    std::stringstream ss;
    ss << std::cin.rdbuf();
    std::string w; int n = 0;
    while (ss >> w) n++;
    std::cout << n << std::endl;
    return 0;
}
