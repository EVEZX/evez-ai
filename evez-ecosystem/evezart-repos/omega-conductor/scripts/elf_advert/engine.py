from scripts.elf_advert.engine import generate_batch, get_queue_stats
import sys, json

target = sys.argv[1] if len(sys.argv) > 1 else 'EVEZ'
n = int(sys.argv[2]) if len(sys.argv) > 2 else 5
variants = generate_batch(target, n)
print(json.dumps({'variants': len(variants), 'batch_id': variants[0]['batch_id']}, indent=2))
