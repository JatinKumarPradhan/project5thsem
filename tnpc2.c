#include <stdio.h>

int main() {
    int totalSeconds, hours, minutes, seconds;

    printf("Enter the number of seconds: ");
    scanf("%d", &totalSeconds);

    hours = totalSeconds / 3600;
    totalSeconds %= 3600;
    minutes = totalSeconds / 60;
    seconds = totalSeconds % 60;

    printf("The time is: %02d:%02d:%02d\n", hours, minutes, seconds);
    return 0;
}