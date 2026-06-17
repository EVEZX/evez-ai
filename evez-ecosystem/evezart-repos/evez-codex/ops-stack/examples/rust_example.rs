use serde::Serialize;
use serde_jcs;

#[derive(Serialize)]
struct MarketData {
    market: String,
    ticker: String,
    price: i32,
    timestamp: i64,
    volume: i32,
}

fn main() {
    // Sample data
    let data = MarketData {
        market: "cryptocurrency".to_string(),
        ticker: "BTC-USD".to_string(),
        price: 50000,
        timestamp: 1234567890,
        volume: 1000000,
    };
    
    // Canonicalize
    let canonical = serde_jcs::to_string(&data).expect("Failed to canonicalize");
    
    println!("Rust Canonical JSON Example");
    println!("{}", "=".repeat(50));
    println!("Canonical:     {}", canonical);
    println!("{}", "=".repeat(50));
    
    // Verify deterministic output
    let canonical2 = serde_jcs::to_string(&data).expect("Failed to canonicalize");
    assert_eq!(canonical, canonical2, "Canonicalization is not deterministic!");
    
    println!("✅ Canonicalization is deterministic");
}
