package main

import (
	"net/http"
)

func main() {
	http.HandleFunc("/", Handle)
	if err := http.ListenAndServe(":8080", nil); err != nil {
		panic(err)
	}
}
