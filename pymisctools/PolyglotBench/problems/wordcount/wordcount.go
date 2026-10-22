package main
import (
    "bufio"
    "fmt"
    "io"
    "os"
    "strings"
)
func main() {
    data, _ := io.ReadAll(bufio.NewReader(os.Stdin))
    fmt.Println(len(strings.Fields(string(data))))
}
