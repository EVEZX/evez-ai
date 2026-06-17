// hash_emitter.go
// EVEZ B1 Cross-Runtime Verification - Go canonical hash emitter
//
// Note: This uses a simplified normalization (no full NFC) since Go's stdlib
// doesn't include NFC normalization. For production, use golang.org/x/text.

package main

import (
	"crypto/sha256"
	"encoding/hex"
	"encoding/json"
	"fmt"
	"io/ioutil"
	"os"
	"sort"
)

// Result for each file
type FileResult struct {
	Hash  string `json:"hash"`
	Error string `json:"error"`
}

// normalizeJSON recursively sorts object keys (simplified normalization)
func normalizeJSON(obj interface{}) interface{} {
	switch v := obj.(type) {
	case string:
		return v
	case []interface{}:
		result := make([]interface{}, len(v))
		for i, elem := range v {
			result[i] = normalizeJSON(elem)
		}
		return result
	case map[string]interface{}:
		keys := make([]string, 0, len(v))
		for k := range v {
			keys = append(keys, k)
		}
		sort.Strings(keys)
		result := make(map[string]interface{})
		for _, k := range keys {
			result[k] = normalizeJSON(v[k])
		}
		return result
	default:
		return v
	}
}

func canonicalHash(path string) (string, error) {
	data, err := ioutil.ReadFile(path)
	if err != nil {
		return "", err
	}

	var obj interface{}
	if err := json.Unmarshal(data, &obj); err != nil {
		return "", err
	}

	normalized := normalizeJSON(obj)
	canonical, err := json.Marshal(normalized)
	if err != nil {
		return "", err
	}

	hash := sha256.Sum256(canonical)
	return "sha256:" + hex.EncodeToString(hash[:]), nil
}

func main() {
	files := os.Args[1:]
	results := make(map[string]FileResult)

	for _, file := range files {
		h, err := canonicalHash(file)
		if err != nil {
			results[file] = FileResult{Hash: "", Error: err.Error()}
		} else {
			results[file] = FileResult{Hash: h, Error: ""}
		}
	}

	output, _ := json.MarshalIndent(results, "", "  ")
	fmt.Println(string(output))
}