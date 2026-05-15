# test_store_verify.py
from app.blockchain.contract_client import ContractClient
import hashlib, json

c = ContractClient(abi_path='app/blockchain/contract_abi.json')

# sample hex-hash (use your real computed SHA256 hex string)
sample = hashlib.sha256(b"test-video").hexdigest()
hexhash = "0x" + sample  # if your contract expects string without 0x, pass sample (string)
print("sample hash:", sample)

# NOTE: Your Solidity uses string type; pass plain string (no 0x) if that's what you used to store
try:
    # try verify before storing
    before = c.verify_hash(sample)
    print("verify before storing:", before)
except Exception as e:
    print("verify failed:", e)

try:
    receipt = c.store_hash(sample)  # uses default account
    print("store tx receipt:", receipt.transactionHash.hex())
except Exception as e:
    print("store failed:", e)

try:
    after = c.verify_hash(sample)
    print("verify after storing:", after)
except Exception as e:
    print("verify failed after store:", e)
