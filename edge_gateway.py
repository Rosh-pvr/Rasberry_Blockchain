import serial
from flask import Flask, request, jsonify
import threading
import time
from web3 import Web3

app = Flask(__name__)

# --- CONFIGURATION ---
# Replace with your actual Arduino Serial Port (usually /dev/ttyUSB0 or /dev/ttyACM0)
arduino_port = '/dev/ttyACM0' 
baud_rate = 115200

# 1. ARDUINO LISTENER (Wired - DHT Sensor)
def listen_to_arduino():
    try:
        ser = serial.Serial(arduino_port, baud_rate, timeout=1)
        print(f"[*] Listening to Arduino on {arduino_port}...")
        while True:
            if ser.in_waiting > 0:
                line = ser.readline().decode('utf-8').rstrip()
                # Example data: "TEMP:25.5,HUM:60.2"
                print(f"[DHT DATA - ROUTINE]: {line}")
                # Future Step: Send this to the Blockchain as a Low-Priority Transaction
    except Exception as e:
        print(f"[!] Arduino Error: {e}")

# 2. ESP32 LISTENER (Wireless - PIR Sensor)
# Replace 'YOUR_CONTRACT_ADDRESS' with the one from the deployment script
contract_address = "0xdB7d6AB1f17c6b31909aE466702703dAEf9269Cf" 
abi = [
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
]# Copy this from the terminal output of your deployment script

contract = w3.eth.contract(address=contract_address, abi=abi)

@app.route('/motion', methods=['POST'])
def motion_alert():
    data = request.json
    priority = 2 if data.get('priority') == 'high' else 1
    
    # Call the Blockchain Smart Contract
    tx_hash = contract.functions.requestAccess("PIR_Sensor", priority).transact()
    print(f"[!!!] Resource Allocated via Blockchain. TX: {tx_hash.hex()}")
    
    return jsonify({"status": "Success", "tx": tx_hash.hex()}), 200

if __name__ == '__main__':
    # Start the Arduino listener in a separate thread so it doesn't block the API
    arduino_thread = threading.Thread(target=listen_to_arduino)
    arduino_thread.daemon = True
    arduino_thread.start()

    # Start the Flask Server (The Edge Gateway)
    print("[*] Edge Gateway is live. Connect ESP32 to this IP on port 5000.")
    app.run(host='0.0.0.0', port=5000)
    
