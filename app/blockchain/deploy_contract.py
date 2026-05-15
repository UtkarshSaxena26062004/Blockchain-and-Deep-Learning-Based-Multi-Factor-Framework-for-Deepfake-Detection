# from web3 import Web3
# from solcx import compile_standard, install_solc
# import json

# GANACHE_URL = 'http://127.0.0.1:7545'

# def compile_and_deploy(sol_path):
#     install_solc('0.8.10')
#     with open(sol_path, 'r') as f:
#         source = f.read()
#     compiled = compile_standard({
#         'language': 'Solidity',
#         'sources': {'VideoVerification.sol': {'content': source}},
#         'settings': {'outputSelection': {'*': {'*': ['abi','evm.bytecode']}}}
#     }, solc_version='0.8.10')

#     abi = compiled['contracts']['VideoVerification.sol']['VideoVerification']['abi']
#     bytecode = compiled['contracts']['VideoVerification.sol']['VideoVerification']['evm']['bytecode']['object']

#     w3 = Web3(Web3.HTTPProvider(GANACHE_URL))
#     acct = w3.eth.accounts[0]
#     Video = w3.eth.contract(abi=abi, bytecode=bytecode)
#     tx_hash = Video.constructor().transact({'from': acct})
#     tx_receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
#     address = tx_receipt.contractAddress
#     print('Deployed at', address)
#     with open('app/blockchain/contract_abi.json','w') as f:
#         json.dump({'abi':abi,'address':address}, f)
#     return abi, address

# if __name__ == '__main__':
#     compile_and_deploy('app/blockchain/VideoVerification.sol')

# deploy_contract.py
import json
from web3 import Web3

RPC = "http://127.0.0.1:7545"   # Ganache RPC
ABI_PATH = "app/blockchain/contract_abi.json"

# 1) Ganache se connect
w3 = Web3(Web3.HTTPProvider(RPC))
if not (w3.is_connected() if hasattr(w3, "is_connected") else w3.isConnected()):
    raise RuntimeError("Ganache se connect nahi ho paaya. Kya Ganache chal raha hai?")

print("✅ Connected to Ganache")

# 2) ABI + bytecode load karo
with open(ABI_PATH) as f:
    data = json.load(f)

abi = data.get("abi")
bytecode = data.get("bytecode")

if not abi:
    raise RuntimeError("ABI not found in contract_abi.json (key: 'abi').")

if not bytecode:
    raise RuntimeError("Bytecode not found in contract_abi.json (key: 'bytecode').")

# 3) Deployer account choose karo (Ganache ka account[0])
deployer = w3.eth.accounts[0]
print("Using deployer account:", deployer)

# 4) Contract object banao
Contract = w3.eth.contract(abi=abi, bytecode=bytecode)

# 5) Deploy transaction bhejo
print("⏳ Deploying contract, please wait...")
tx_hash = Contract.constructor().transact({
    "from": deployer,
    "gas": 6_000_000
})

print("TX hash:", tx_hash.hex())
tx_receipt = w3.eth.wait_for_transaction_receipt(tx_hash)

contract_address = tx_receipt.contractAddress
print("✅ Contract deployed at:", contract_address)

# 6) Address ko contract_abi.json me save karo
data["address"] = contract_address

with open(ABI_PATH, "w") as f:
    json.dump(data, f, indent=2)

print("✅ Saved contract address into", ABI_PATH)
