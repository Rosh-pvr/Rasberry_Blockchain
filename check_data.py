from web3 import Web3

# Connection setup
w3 = Web3(Web3.HTTPProvider('http://127.0.0.1:8545'))
CONTRACT_ADDRESS = "0xdB7d6AB1f17c6b31909aE466702703dAEf9269Cf"

# Use your existing ABI here
ABI = [
  {
    "inputs": [],
    "stateMutability": "nonpayable",
    "type": "constructor"
  },
  {
    "anonymous": False,
    "inputs": [
      {
        "indexed": False,
        "internalType": "uint256",
        "name": "requestId",
        "type": "uint256"
      },
      {
        "indexed": False,
        "internalType": "string",
        "name": "sensor",
        "type": "string"
      },
      {
        "indexed": False,
        "internalType": "uint256",
        "name": "priority",
        "type": "uint256"
      }
    ],
    "name": "ResourceAllocated",
    "type": "event"
  },
  {
    "inputs": [],
    "name": "edgeNode",
    "outputs": [
      {
        "internalType": "address",
        "name": "",
        "type": "address"
      }
    ],
    "stateMutability": "view",
    "type": "function"
  },
  {
    "inputs": [],
    "name": "requestCount",
    "outputs": [
      {
        "internalType": "uint256",
        "name": "",
        "type": "uint256"
      }
    ],
    "stateMutability": "view",
    "type": "function"
  },
  {
    "inputs": [
      {
        "internalType": "string",
        "name": "_sensor",
        "type": "string"
      },
      {
        "internalType": "uint256",
        "name": "_priority",
        "type": "uint256"
      }
    ],
    "name": "requestResource",
    "outputs": [],
    "stateMutability": "nonpayable",
    "type": "function"
  },
  {
    "inputs": [
      {
        "internalType": "uint256",
        "name": "",
        "type": "uint256"
      }
    ],
    "name": "requests",
    "outputs": [
      {
        "internalType": "address",
        "name": "requester",
        "type": "address"
      },
      {
        "internalType": "string",
        "name": "sensorType",
        "type": "string"
      },
      {
        "internalType": "uint256",
        "name": "priority",
        "type": "uint256"
      },
      {
        "internalType": "bool",
        "name": "allocated",
        "type": "bool"
      }
    ],
    "stateMutability": "view",
    "type": "function"
  }
] 

contract = w3.eth.contract(address=CONTRACT_ADDRESS, abi=ABI)

# Get the total number of entries
count = contract.functions.requestCount().call()

print(f"\n" + "="*50)
print(f"BLOCKCHAIN AUDIT LOG - TOTAL ENTRIES: {count}")
print("="*50)

# We want to see the last 10 transactions
start_index = max(0, count - 10)

for i in range(start_index, count):
    data = contract.functions.requests(i).call()
    sensor = data[1]
    priority = data[2]
    status = "Allocated" if data[3] else "Pending"
    
    # Visual marker to spot the ESP32 quickly
    marker = "!!! [ALERT]" if "ESP32" in sensor else "--- [LOG  ]"
    
    print(f"ID: {i} | {marker} Sensor: {sensor:<12} | Priority: {priority} | Status: {status}")

print("="*50 + "\n")
