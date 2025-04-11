#include <iostream>
#include <string>
#include <cstdio> // For printf

int main() {
    std::string answer;
    std::cout << "Is X black or white? ";
    std::getline(std::cin, answer); // Read user input

    if (answer == "black") {
        printf("black\n");
    } else if (answer == "white") {
        printf("white\n");
    } else {
        printf("Error\n");
    }

    return 0;
}