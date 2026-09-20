from web3 import Web3

w3 = Web3(Web3.HTTPProvider('http://127.0.0.1:8545'))
CONTRACT_ADDRESS = "0xdB7d6AB1f17c6b31909aE466702703dAEf9269Cf"
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
] # (Use your ABI)

contract = w3.eth.contract(address=CONTRACT_ADDRESS, abi=ABI)
count = contract.functions.requestCount().call()

print(f"Searching {count} entries for ESP32 alerts...")
found = False

for i in range(count):
    data = contract.functions.requests(i).call()
    if "ESP32" in data[1]:
        print(f"FOUND! ID: {i} | Sensor: {data[1]} | Priority: {data[2]}")
        found = True

if not found:
    print("No ESP32 data found in the entire history. Let's troubleshoot connectivity.")
