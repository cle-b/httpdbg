package indir

import (
	"fmt"
	"log"
	"net/http"
)

func AnotherFunction(url string) {
	resp, err := http.Get(url)
	if err != nil {
		log.Fatalf("Error making HTTP request in AnotherFunction: %v", err)
	}
	defer resp.Body.Close()

	fmt.Printf("mymod.go: Response status from %s: %s\n", url, resp.Status)
}
