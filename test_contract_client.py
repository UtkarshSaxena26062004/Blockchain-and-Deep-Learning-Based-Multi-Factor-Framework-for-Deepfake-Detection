# test_contract_client.py
from app.blockchain.contract_client import ContractClient

try:
    c = ContractClient(abi_path='app/blockchain/contract_abi.json')
    print("Contract client initialized OK")
    print("Contract address:", c.address)
    # safe way to list functions
    print("Contract functions:", [item['name'] for item in c.contract.abi if item.get('type') == 'function'])
except Exception as e:
    print("Init error:", e)
    import traceback; traceback.print_exc()
