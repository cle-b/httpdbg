package main

import (
	"fmt"
	"log"
	"net/http"
	"os"

	"demo_go/indir"
)

func main() {
	if len(os.Args) < 2 {
		log.Fatal("Usage: go run main.go <URL>")
	}
	url := os.Args[1]

	resp, err := http.Get(url)
	if err != nil {
		log.Fatalf("Error making HTTP request: %v", err)
	}
	defer resp.Body.Close()

	fmt.Printf("main.go: Response status from %s: %s\n", url, resp.Status)

	indir.AnotherFunction(url)
}
