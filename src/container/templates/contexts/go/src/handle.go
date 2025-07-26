package main

import (
	"fmt"
	"net/http"
)

// Handle an HTTP Request.
func Handle(w http.ResponseWriter, r *http.Request) {
	/*
	 * YOUR CODE HERE
	 */
	fmt.Println("Static HTTP handler invoked")
	fmt.Fprintln(w, "Static HTTP Handler invoked")
}
