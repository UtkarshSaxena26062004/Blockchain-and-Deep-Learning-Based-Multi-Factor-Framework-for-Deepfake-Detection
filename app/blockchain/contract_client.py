from web3 import Web3
import json, os, traceback

GANACHE_URL = 'http://127.0.0.1:7545'  # make sure this matches Ganache RPC

class ContractClient:
    def __init__(self, abi_path='app/blockchain/contract_abi.json'):
        self.abi_path = abi_path
        if not os.path.exists(abi_path):
            raise FileNotFoundError(f"ABI file not found: {abi_path}")
        with open(abi_path, 'r') as f:
            data = json.load(f)
        # support both shapes: {abi:, address:} or abi (list) + address separate
        self.abi = data.get('abi') if isinstance(data, dict) else data
        self.address_raw = data.get('address') if isinstance(data, dict) else None

        self.w3 = Web3(Web3.HTTPProvider(GANACHE_URL))
        if not self.w3.is_connected():
            raise ConnectionError(f"Web3 not connected to {GANACHE_URL}")

        # Accounts list (Ganache provides unlocked accounts)
        try:
            self.accounts = self.w3.eth.accounts
        except Exception:
            self.accounts = []
        if not self.accounts:
            # not fatal but warn
            print("Warning: no accounts available via provider. Frontend signing may be required.")

        # normalize address
        if not self.address_raw:
            raise ValueError("Contract address missing in ABI JSON (key 'address')")
        try:
            self.address = self.w3.to_checksum_address(self.address_raw)
        except Exception as e:
            raise ValueError(f"Invalid contract address '{self.address_raw}': {e}")

        # check for bytecode at address
        code = self.w3.eth.get_code(self.address)
        print("Contract bytecode length at address:", len(code))
        if len(code) == 0:
            raise RuntimeError(f"No contract bytecode found at {self.address} - deploy the contract first")

        # instantiate contract
        self.contract = self.w3.eth.contract(address=self.address, abi=self.abi)

        # pick default account
        self.account = self.accounts[0] if self.accounts else None
        print("Using account:", self.account)

    def store_hash(self, hexhash, from_account=None, gas=300000):
        from_account = from_account or self.account
        if not from_account:
            raise RuntimeError("No account available to send transactions from.")
        try:
            tx = self.contract.functions.storeHash(hexhash).transact({'from': from_account, 'gas': gas})
            receipt = self.w3.eth.wait_for_transaction_receipt(tx)
            print("store_hash tx mined:", receipt.transactionHash.hex())
            return receipt
        except Exception as e:
            print("store_hash failed:", e)
            print(traceback.format_exc())
            raise

    def verify_hash(self, hexhash):
        try:
            return self.contract.functions.verifyHash(hexhash).call()
        except Exception as e:
            print("verify_hash failed:", e)
            print(traceback.format_exc())
            raise
