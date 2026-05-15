# app/blockchain/deploy.py
from solcx import compile_standard, install_solc
from web3 import Web3
import json, os, sys

GANACHE_URL = 'http://127.0.0.1:7545'
SOLC_VERSION = "0.8.10"

def compile_and_deploy(sol_path):
    print("Installing solc", SOLC_VERSION, "if needed...")
    install_solc(SOLC_VERSION)
    with open(sol_path, 'r', encoding='utf-8') as f:
        source = f.read()

    print("Compiling contract...")
    compiled = compile_standard({
        'language': 'Solidity',
        'sources': {os.path.basename(sol_path): {'content': source}},
        'settings': {
            'outputSelection': {
                '*': {
                    '*': ['abi', 'evm.bytecode']
                }
            }
        }
    }, solc_version=SOLC_VERSION)

    contract_name = list(compiled['contracts'][os.path.basename(sol_path)].keys())[0]
    contract_data = compiled['contracts'][os.path.basename(sol_path)][contract_name]
    abi = contract_data['abi']
    bytecode = contract_data['evm']['bytecode']['object']

    w3 = Web3(Web3.HTTPProvider(GANACHE_URL))
    if not w3.is_connected():
        raise RuntimeError(f"Could not connect to Ganache at {GANACHE_URL} - start Ganache and retry")

    acct = w3.eth.accounts[0]
    print("Using account:", acct)

    Contract = w3.eth.contract(abi=abi, bytecode=bytecode)
    print("Deploying contract (this may take a few seconds)...")
    tx_hash = Contract.constructor().transact({'from': acct})
    receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
    address = receipt.contractAddress
    print("Deployed at:", address)

    out = {'abi': abi, 'address': address}
    out_path = os.path.join(os.path.dirname(__file__), 'contract_abi.json')
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(out, f, indent=2)
    print("Wrote ABI+address to", out_path)
    return abi, address

if __name__ == "__main__":
    sol_file = os.path.join(os.path.dirname(__file__), 'VideoVerification.sol')
    if not os.path.exists(sol_file):
        print("ERROR: Solidity file not found at", sol_file)
        sys.exit(1)
    compile_and_deploy(sol_file)
