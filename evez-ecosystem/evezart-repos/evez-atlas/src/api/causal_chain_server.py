from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path

module_path = Path(__file__).with_name("causal-chain-server.py")
spec = spec_from_file_location("causal_chain_server_impl", module_path)
module = module_from_spec(spec)
spec.loader.exec_module(module)

app = module.app
hmac_sign = module.hmac_sign
