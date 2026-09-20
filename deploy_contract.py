from web3 import Web3
from solcx import compile_source, install_solc

# Install specific Solidity version
install_solc('0.8.0')

# The Smart Contract Logic (from BARA framework)
contract_source_code = '''
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

contract ResourceBroker {
    struct Request {
        string sensor;
        uint256 priority;
        uint256 timestamp;
    }
    Request[] public history;

    event ResourceAllocated(string sensor, uint256 priority);

    function requestAccess(string memory _sensor, uint256 _priority) public {
        history.push(Request(_sensor, _priority, block.timestamp));
        emit ResourceAllocated(_sensor, _priority);
    }
}
'''

# Connect to your Dev Node
w3 = Web3(Web3.HTTPProvider('http://127.0.0.1:8545'))
w3.eth.default_account = w3.eth.accounts[0]

# Compile and Deploy
compiled_sol = compile_source(contract_source_code, solc_version='0.8.0')
contract_id, contract_interface = compiled_sol.popitem()

ResourceBroker = w3.eth.contract(abi=contract_interface['abi'], bytecode=contract_interface['bin'])
tx_hash = ResourceBroker.constructor().transact()
tx_receipt = w3.eth.wait_for_transaction_receipt(tx_hash)

print(f"[*] Contract Deployed at: {tx_receipt.contractAddress}")
# SAVE THIS ADDRESS FOR THE NEXT STEP!
