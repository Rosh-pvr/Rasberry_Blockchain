import serial
import time
import threading
import json
from flask import Flask, request, jsonify
from web3 import Web3
from web3.middleware import ExtraDataToPOAMiddleware

app = Flask(__name__)

# --- 1. BLOCKCHAIN CONFIGURATION ---
w3 = Web3(Web3.HTTPProvider('http://127.0.0.1:8545'))
w3.eth.default_account = w3.eth.accounts[0]
w3.middleware_onion.inject(ExtraDataToPOAMiddleware, layer=0)

# IMPORTANT: Paste your specific data here
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
]

contract = w3.eth.contract(address=CONTRACT_ADDRESS, abi=ABI)

# --- 2. THE WIFI GATEWAY (For ESP32) ---
@app.route('/motion', methods=['POST'])
def handle_motion():
    # This will print EVERY time a request hits the Pi, even if the data is bad
    print(f"\n[!] INCOMING REQUEST from {request.remote_addr}")
    
    try:
        # Don't even check the JSON yet, just try the blockchain
        print("[!] ALERT: Motion Detected! Writing to Blockchain...")
        tx_hash = contract.functions.requestResource("ESP32_PIR", 2).transact()
        
        # We don't wait for receipt here to keep it fast
        return jsonify({"status": "Sent", "tx": tx_hash.hex()}), 200
    except Exception as e:
        print(f"[!] WiFi Route Error: {e}")
        return jsonify({"error": str(e)}), 500

# --- 3. THE SERIAL LISTENER (For Arduino) ---
def arduino_listener():
    print("[*] Serial Thread: Attempting to open /dev/ttyACM0...")
    try:
        ser = serial.Serial('/dev/ttyACM0', 115200, timeout=1)
        ser.flush()
        print("[SUCCESS] Serial Thread: Connected to Arduino!")
        
        while True:
            if ser.in_waiting > 0:
                line = ser.readline().decode('latin-1').strip()
                # If we see ANY text, print it immediately for debugging
                print(f"ARDUINO SAYS: {line}") 
                
                if "TEMP" in line.upper():
                    print("[+] Sending DHT to Blockchain...")
                    tx = contract.functions.requestResource("ARDUINO_DHT", 1).transact()
                    print(f"[*] TX Hash: {tx.hex()[:10]}")
            time.sleep(0.1)
    except Exception as e:
        print(f"[!] SERIAL ERROR: {e}")
        print("[?] Tip: Try changing /dev/ttyACM0 to /dev/ttyUSB0 in the code.")

# --- 4. EXECUTION ---
if __name__ == '__main__':
    # 1. Start Arduino listener in the background
    serial_thread = threading.Thread(target=arduino_listener, daemon=True)
    serial_thread.start()

    # 2. Start Flask for the ESP32 on the Pi's IP
    print("\n" + "="*40)
    print("EDGE GATEWAY ACTIVE")
    print("Listening for ESP32 on port 5000")
    print("Listening for Arduino on /dev/ttyACM0")
    print("="*40 + "\n")
    
    app.run(host='0.0.0.0', port=5000)
