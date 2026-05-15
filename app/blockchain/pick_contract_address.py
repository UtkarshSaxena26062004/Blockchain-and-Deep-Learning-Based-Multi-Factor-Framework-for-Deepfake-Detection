# pick_contract_address.py  (fixed, robust checksum handling)
import json, os
from web3 import Web3

RPC = "http://127.0.0.1:7545"   # change if needed
ABI_PATH = "app/blockchain/contract_abi.json"

candidates = [
    "0x3F8E6087AB8f48Ac3404d845DdBC0587d2435358",
    "0xC6d25483D6bcfB57C12c2B08232A5d1e4729480c",
    "0x661ce6542f0e1096E5173b24626EeC18486Da5eB",
    "0x9E992feca994C4eC40F4cA29e60bb04E7b55869A",
    "0x7D91cAc5A497148c3261B6f05A1A120D2dF73Edf",
    "0xADc5277E450228a51A038B3A0fbbB91F179376E0",
    "0xE7516093FAEF720958041A7D68764e7b777C7420",
    "0x242420e5E726c95b63E6643b24E38220B4460863",
    "0x5B9fFD666cF83348777da31355b3BCaAB16500ed",
    "0xe759D7e6f635466faa537278Fb6112CE30CEcA7c",
]

w3 = Web3(Web3.HTTPProvider(RPC))
print("Connected:", (w3.isConnected() if hasattr(w3, "isConnected") else w3.is_connected()))

# append node accounts to candidates so we check them too
try:
    node_accounts = list(w3.eth.accounts)
    print("Node has", len(node_accounts), "accounts.")
    for a in node_accounts:
        if a not in candidates:
            candidates.append(a)
except Exception as e:
    print("Could not fetch node accounts:", e)

def checksum(addr):
    """Robust checksum that works across web3.py versions."""
    try:
        # class method
        return Web3.toChecksumAddress(addr)
    except Exception:
        pass
    try:
        # instance method (newer naming)
        return w3.to_checksum_address(addr)
    except Exception:
        pass
    try:
        # older instance method
        return w3.toChecksumAddress(addr)
    except Exception:
        pass
    # last resort, return original (may fail later)
    return addr

found = None
for addr in candidates:
    try:
        chk = checksum(addr)
        code = w3.eth.get_code(chk)
        print(f"{chk} : code length = {len(code)}")
        if len(code) > 0 and found is None:
            found = chk
    except Exception as e:
        print(f"{addr} -> error: {e}")

if found:
    print("Found deployed contract at:", found)
    if os.path.exists(ABI_PATH):
        data = json.load(open(ABI_PATH))
        if isinstance(data, dict):
            data['address'] = found
            with open(ABI_PATH, 'w') as f:
                json.dump(data, f, indent=2)
            print("Wrote new address into", ABI_PATH)
        else:
            print(ABI_PATH, "is not an object; not updating")
else:
    print("No contract bytecode found at any candidate address on this node.")
    print("If no address found, redeploy the contract (see Option B).")
# pick_contract_address.py  (fixed, robust checksum handling)
import json, os
from web3 import Web3

RPC = "http://127.0.0.1:7545"   # change if needed
ABI_PATH = "app/blockchain/contract_abi.json"

candidates = [
    "0x3F8E6087AB8f48Ac3404d845DdBC0587d2435358",
    "0xC6d25483D6bcfB57C12c2B08232A5d1e4729480c",
    "0x661ce6542f0e1096E5173b24626EeC18486Da5eB",
    "0x9E992feca994C4eC40F4cA29e60bb04E7b55869A",
    "0x7D91cAc5A497148c3261B6f05A1A120D2dF73Edf",
    "0xADc5277E450228a51A038B3A0fbbB91F179376E0",
    "0xE7516093FAEF720958041A7D68764e7b777C7420",
    "0x242420e5E726c95b63E6643b24E38220B4460863",
    "0x5B9fFD666cF83348777da31355b3BCaAB16500ed",
    "0xe759D7e6f635466faa537278Fb6112CE30CEcA7c",
]

w3 = Web3(Web3.HTTPProvider(RPC))
print("Connected:", (w3.isConnected() if hasattr(w3, "isConnected") else w3.is_connected()))

# append node accounts to candidates so we check them too
try:
    node_accounts = list(w3.eth.accounts)
    print("Node has", len(node_accounts), "accounts.")
    for a in node_accounts:
        if a not in candidates:
            candidates.append(a)
except Exception as e:
    print("Could not fetch node accounts:", e)

def checksum(addr):
    """Robust checksum that works across web3.py versions."""
    try:
        # class method
        return Web3.toChecksumAddress(addr)
    except Exception:
        pass
    try:
        # instance method (newer naming)
        return w3.to_checksum_address(addr)
    except Exception:
        pass
    try:
        # older instance method
        return w3.toChecksumAddress(addr)
    except Exception:
        pass
    # last resort, return original (may fail later)
    return addr

found = None
for addr in candidates:
    try:
        chk = checksum(addr)
        code = w3.eth.get_code(chk)
        print(f"{chk} : code length = {len(code)}")
        if len(code) > 0 and found is None:
            found = chk
    except Exception as e:
        print(f"{addr} -> error: {e}")

if found:
    print("Found deployed contract at:", found)
    if os.path.exists(ABI_PATH):
        data = json.load(open(ABI_PATH))
        if isinstance(data, dict):
            data['address'] = found
            with open(ABI_PATH, 'w') as f:
                json.dump(data, f, indent=2)
            print("Wrote new address into", ABI_PATH)
        else:
            print(ABI_PATH, "is not an object; not updating")
else:
    print("No contract bytecode found at any candidate address on this node.")
    print("If no address found, redeploy the contract (see Option B).")
