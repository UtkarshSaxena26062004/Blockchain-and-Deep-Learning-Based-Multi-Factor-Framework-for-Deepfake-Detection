from web3 import Web3

ganache_url = "http://127.0.0.1:7545"
w3 = Web3(Web3.HTTPProvider(ganache_url))

print("Connected:", w3.is_connected())
print("Accounts:", w3.eth.accounts)
print("Chain ID:", w3.eth.chain_id)

contract_address = "0xYourContractAddressHere"   # replace your address
contract_address = Web3.to_checksum_address(contract_address)

print("Checksum Address:", contract_address)
