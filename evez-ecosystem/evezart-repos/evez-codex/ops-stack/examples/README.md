# Ops Stack - Language Examples

This directory contains example implementations of canonical JSON serialization across multiple languages.

## Examples

- `python_example.py` - Python implementation using rfc8785
- `go_example.go` - Go implementation using webpki/jcs
- `rust_example.rs` - Rust implementation using serde_jcs

## Running Examples

### Python
```bash
python3 examples/python_example.py
```

### Go
```bash
cd examples
go run go_example.go
```

### Rust
```bash
cd examples
rustc rust_example.rs && ./rust_example
```

All examples should produce the same canonical JSON output for equivalent data structures, demonstrating cross-language interoperability.
