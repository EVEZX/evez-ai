# OKTOKLAW Breakaway Shell

**Self-Contained Development, Test, Verify, and Sell Environment**

Takes any Python module dropped into it. Runs it through the EVEZ Invariance Battery (5 rotations). Generates a product manifest. Outputs a ClawHub/Gumroad-ready listing.

No external dependencies required for the test phase. Everything runs in the sandbox.

## Inputs
- `module_path`: path to Python file to test
- `product_name`: what to call it
- `price`: target price (default $25)
- `category`: ClawHub category (default: "AI Tools")

## Outputs
- Test report (all 5 rotations)
- poly_c score
- Product listing (Gumroad markdown)
- FIRE event record if poly_c >= 0.7

## Usage
```
run_skill oktoklaw --module_path agents/stripe_integration.py --product_name "EVEZ Stripe Bridge" --price 50
```
