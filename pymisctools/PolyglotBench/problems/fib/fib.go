package main
import (
    "bufio"
    "fmt"
    "os"
    "strconv"
    "strings"
)
func main() {
    sc := bufio.NewScanner(os.Stdin)
    sc.Scan()
    n, _ := strconv.Atoi(strings.TrimSpace(sc.Text()))
    a, b := 0, 1
    for i := 0; i < n; i++ { a, b = b, a+b }
    fmt.Println(a)
}
