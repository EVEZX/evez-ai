package main

import (
	"encoding/json"
	"fmt"
	
	"github.com/cyberphone/json-canonicalization/go/src/webpki.org/jsoncanonicalizer"
)

func main() {
	// Sample data
	data := map[string]interface{}{
		"market":    "cryptocurrency",
		"ticker":    "BTC-USD",
		"price":     50000,
		"timestamp": 1234567890,
		"volume":    1000000,
	}
	
	// Convert to JSON bytes
	jsonBytes, err := json.Marshal(data)
	if err != nil {
		panic(err)
	}
	
	// Canonicalize
	canonical, err := jsoncanonicalizer.Transform(jsonBytes)
	if err != nil {
		panic(err)
	}
	
	fmt.Println("Go Canonical JSON Example")
	fmt.Println("==================================================")
	fmt.Printf("Original data: %s\n", jsonBytes)
	fmt.Printf("Canonical:     %s\n", canonical)
	fmt.Println("==================================================")
	
	// Verify deterministic output
	canonical2, _ := jsoncanonicalizer.Transform(jsonBytes)
	if string(canonical) != string(canonical2) {
		panic("Canonicalization is not deterministic!")
	}
	
	fmt.Println("✅ Canonicalization is deterministic")
}
