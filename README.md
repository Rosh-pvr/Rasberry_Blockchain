Secure Edge IoT Sensor Ledger with Raspberry Pi, Geth & Smart Contracts
A lightweight edge-IoT security and audit architecture that collects sensor events at a Raspberry Pi gateway and records trusted event metadata on a private Ethereum-compatible blockchain.

![BlockDiagram_BLOCKCHAIN_TECH](https://drive.google.com/file/d/1j-PlslAvrufJRo-IH9HlVAwrdx4x-Fro/view?usp=drive_link "This is a blockdiagram for blockchain")


1. Project Overview
This project implements a blockchain-backed edge gateway for IoT sensor events.
The Raspberry Pi acts as the edge node between field devices and a private Ethereum-compatible blockchain. Two sensing paths are represented in the implementation:
·	Arduino + DHT sensor → sends temperature/humidity readings over USB serial.
·	ESP32 + PIR sensor → sends motion events over Wi-Fi using an HTTP request.
The Raspberry Pi receives these events and uses Web3.py to submit a transaction to a Solidity smart contract running on a local Geth blockchain. The contract maintains a ledger of sensor/resource requests, including the originating account, sensor type, priority, and allocation status.
The design therefore separates the system into three layers:
1.	Sensing layer – Arduino/DHT and ESP32/PIR.
2.	Edge security/gateway layer – Raspberry Pi, Python, Flask, Web3.py and serial handling.
3.	Trust/audit layer – Geth private blockchain + Solidity smart contract.
Core objective
The project demonstrates how a constrained edge device can mediate IoT events and create a tamper-evident audit trail without requiring the sensors themselves to run blockchain software.
Important implementation detail: the current smart contract does not store raw DHT temperature/humidity values. A DHT message containing TEMP causes the gateway to write an ARDUINO_DHT event with priority 1. A PIR event writes an ESP32_PIR event with priority 2. The raw sensor payload remains off-chain in the current implementation.

2. High-Level Architecture
flowchart LR
    subgraph Sensors[IoT / Sensor Layer]
        DHT[Arduino + DHT Sensor\nTemperature / Humidity]
        PIR[ESP32 + PIR Sensor\nMotion]
    end

    subgraph Edge[Raspberry Pi Edge Gateway]
        SERIAL[USB Serial Listener\n/dev/ttyACM0 : 115200]
        FLASK[Flask API\nPOST /motion : 5000]
        WEB3[Web3.py\nTransaction Client]
    end

    subgraph Chain[Private Blockchain]
        GETH[Geth JSON-RPC\n127.0.0.1:8545]
        SC[ResourceAuction.sol\nSmart Contract]
        LEDGER[(On-chain Ledger)]
    end

    DHT -->|TEMP:..., HUM:...| SERIAL
    PIR -->|HTTP POST over Wi-Fi| FLASK
    SERIAL -->|requestResource\nARDUINO_DHT, priority 1| WEB3
    FLASK -->|requestResource\nESP32_PIR, priority 2| WEB3
    WEB3 -->|JSON-RPC| GETH
    GETH --> SC
    SC --> LEDGER

    AUDIT[Audit & Export Scripts\ncheck_data.py\nfind_esp32.py\ndata_export.py] -->|read contract state| WEB3

What happens in practice?
DHT path
DHT sensor → Arduino → USB serial → Raspberry Pi → Web3.py → Geth → smart contract → ledger
PIR path
PIR sensor → ESP32 → Wi-Fi → Flask /motion → Web3.py → Geth → smart contract → ledger

3. Runtime Data Flow
sequenceDiagram
    autonumber
    participant D as DHT / Arduino
    participant P as PIR / ESP32
    participant R as Raspberry Pi
    participant G as Geth
    participant C as ResourceAuction
    participant L as Blockchain Ledger

    D->>R: Serial line: TEMP:25.5,HUM:60.2
    R->>C: requestResource("ARDUINO_DHT", 1)
    C->>L: Store request + emit ResourceAllocated

    P->>R: POST /motion
    R->>C: requestResource("ESP32_PIR", 2)
    C->>L: Store request + emit ResourceAllocated

    L-->>R: Transaction available for auditing

The current gateway intentionally does not wait for a transaction receipt for PIR requests. This keeps the HTTP response path short; the transaction is submitted to Geth and the returned transaction hash is sent back to the caller.

4. Blockchain Data Model
The active contract in the repository is ResourceAuction.sol.
classDiagram
    class ResourceAuction {
        +address edgeNode
        +uint256 requestCount
        +mapping requests
        +requestResource(string, uint256)
    }

    class ResourceRequest {
        +address requester
        +string sensorType
        +uint256 priority
        +bool allocated
    }

    ResourceAuction "1" --> "many" ResourceRequest : stores

On-chain record
Each stored request contains:
Field	Meaning
requester	Ethereum address that submitted the transaction
sensorType	Logical source name, e.g. ARDUINO_DHT or ESP32_PIR
priority	1 = routine sensor event; 2 = critical/motion event in the project convention
allocated	Boolean allocation state; current contract sets this to true for every request

The contract also emits:
ResourceAllocated(uint256 requestId, string sensor, uint256 priority)

This event can be used by monitoring or auditing applications.
Priority semantics
The current convention is:
Sensor/event	Priority	Meaning
Arduino DHT	1	Routine environmental telemetry event
ESP32 PIR	2	Higher-priority motion event

The present smart contract records this priority but does not run a separate scheduler or deny/approve requests based on it. In other words, the blockchain state models the allocation decision; an external resource scheduler is not implemented in the current repository.

5. Technology Stack
Layer	Technology	Role
Edge hardware	Raspberry Pi	Central edge gateway and blockchain host
Environmental sensor	DHT + Arduino	Temperature/humidity sensing
Motion sensor	PIR + ESP32	Motion detection and Wi-Fi event submission
Gateway API	Flask	Receives ESP32 HTTP events
Serial communication	PySerial	Reads Arduino output
Blockchain client	Web3.py	Sends/reads smart-contract transactions
Blockchain node	Geth	Runs the private Ethereum-compatible chain
Smart contract	Solidity	Maintains the resource/event ledger
Contract tooling	Remix IDE	Compile/inspect/deploy contract artifacts
Audit/export	Python + CSV	Inspect and export ledger records


6. Repository Structure
Rasberry_blockchain/
├── ResourceAuction.sol          # Active smart contract
├── final_serial.py              # Main edge gateway (Arduino + ESP32 + blockchain)
├── deploy.py                    # Deploy contract using Remix ABI + bytecode
├── manual_deploy.py             # Alternate manual ABI/bytecode deployment
├── deploy_contract.py           # Older ResourceBroker deployment flow
├── edge_gateway.py              # Older/alternate gateway implementation
├── check_data.py                # Read recent blockchain entries
├── find_esp32.py                # Search ledger for ESP32 events
├── data_export.py               # Export ledger entries to CSV
├── blockchain_data.csv          # Sample/exported ledger data
├── find_esp32.py                # ESP32 ledger search utility
├── bin/                          # Bundled Geth + local chain material (see security note)
└── .gitignore

Which files should be used?
For the current implementation, the most direct execution path is:
ResourceAuction.sol → deploy.py/manual_deploy.py → final_serial.py → check_data.py / data_export.py / find_esp32.py
The other deployment/gateway scripts are retained as development/legacy variants.

7. Prerequisites
Hardware
·	Raspberry Pi with Linux and network connectivity
·	Arduino board
·	DHT temperature/humidity sensor
·	ESP32 board
·	PIR motion sensor
·	USB cable between Arduino and Raspberry Pi
·	5 V/3.3 V power appropriate for the selected boards/sensors
Software
·	Python 3
·	Geth-compatible executable for the private chain
·	Git
·	Remix IDE for compiling the Solidity contract
The Python gateway requires at least:
pip install web3 flask pyserial

py-solc-x is only needed when using deploy_contract.py to compile Solidity locally from Python:
pip install py-solc-x


8. Important Reproducibility Note: Geth / Clique
The project bundle contains a Clique-based genesis configuration and an ARM Geth executable intended for Raspberry Pi. The genesis configuration includes:
·	Chain ID: 1234
·	Clique block period: 5 seconds
·	Gas limit: 8,000,000
·	Local/private network configuration
The official Geth documentation currently marks Clique as deprecated since Geth v1.14. Therefore, the exact historical setup in this repository should be treated as a reproducibility environment, not as a recommendation to build a new production system on modern Geth/Clique. For a fresh implementation, consider a currently supported consensus stack or a current permissioned-EVM platform.
For faithful reproduction, use the compatible Geth executable/configuration that belongs to the project rather than assuming a newly installed Geth release will accept the same Clique genesis configuration.
Official references:
·	Geth private networks: https://geth.ethereum.org/docs/fundamentals/private-network
·	Geth Clique status/documentation: https://geth.ethereum.org/docs/tools/clef/clique-signing
·	Geth JSON-RPC: https://geth.ethereum.org/docs/interacting-with-geth/rpc
·	Web3.py PoA middleware: https://web3py.readthedocs.io/en/latest/middleware.html

9. Security Warning Before Publishing to GitHub
Do not publish the blockchain data directories, keystores, private keys, or passwords from a real deployment.
The uploaded project archive contains local chain state, keystore material and a password file under bin/. These are machine-specific credentials/state and should not be pushed to a public GitHub repository.
Before publishing, remove or exclude items such as:
bin/dev_chain/
bin/fresh_dev_chain/
bin/myblockchain/
*/keystore/
password.txt
geth.ipc

A good GitHub repository should normally contain the source code, genesis template, contract source, documentation and non-secret sample data, not live account credentials or private blockchain state.

10. Installation & Execution
The following procedure describes the intended architecture represented by the repository.
Step 1 — Clone the project
git clone https://github.com/Rosh-pvr/Rasberry_Blockchain.git
cd Rasberry_Blockchain

If you are using the project on the Raspberry Pi directly, confirm the Geth executable is appropriate for the Pi:
chmod +x bin/geth
./bin/geth version

If the bundled executable is not suitable for the target Pi/OS, use the compatible Geth build used by the original project rather than an arbitrary current release.

Step 2 — Create a clean Python environment
Do not rely on the bundled virtual environment when moving the project to another machine. Create a new one on the Raspberry Pi:
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install web3 flask pyserial

Optional, only for deploy_contract.py:
pip install py-solc-x

Verify the imports:
python -c "from web3 import Web3; import serial; import flask; print('Python dependencies OK')"


Step 3 — Prepare the private blockchain
For the original project, a custom genesis file is supplied under the Geth bundle:
bin/geth-linux-arm5-1.17.0-0cf3d3ba/genesis.json

Create a clean runtime directory rather than using a development database copied from another machine:
mkdir -p runtime/node
cp bin/geth-linux-arm5-1.17.0-0cf3d3ba/genesis.json runtime/genesis.json

Initialize the chain:
./bin/geth init --datadir runtime/node runtime/genesis.json

Signer account requirement
The Clique genesis file identifies an initial signer in its extraData field. The corresponding private key must exist in the node's keystore for block signing.
Check the account list:
./bin/geth account list --datadir runtime/node

The signer address in the genesis and the account used to sign blocks must correspond.
Never copy a real private key or password into a public repository. If you are rebuilding the chain from scratch, create a new signer account and regenerate the genesis configuration for that account.

Step 4 — Start Geth and expose local JSON-RPC
The Python gateway expects Geth at:
http://127.0.0.1:8545

A local development run should keep JSON-RPC bound to loopback whenever possible. A Clique-style signer invocation follows this pattern:
./bin/geth \
  --datadir runtime/node \
  --networkid 1234 \
  --http \
  --http.addr 127.0.0.1 \
  --http.port 8545 \
  --http.api eth,net,web3,personal,clique,txpool \
  --unlock 0xYOUR_SIGNER_ADDRESS \
  --password /secure/path/password.txt \
  --mine \
  --nodiscover \
  --maxpeers 0

Use the exact command-line flags supported by the compatible Geth build you are reproducing. The important project-level requirements are:
·	private chain initialized from the project genesis
·	signer account available to the node
·	blocks being produced
·	HTTP JSON-RPC on 127.0.0.1:8545
--unlock / HTTP account access is powerful and should only be used in a controlled local test environment. Never expose an unlocked signing account to an untrusted network.

Step 5 — Verify the blockchain RPC
Open another terminal and activate the Python environment:
source .venv/bin/activate

Then test the connection:
python - <<'PY'
from web3 import Web3
w3 = Web3(Web3.HTTPProvider('http://127.0.0.1:8545'))
print('Connected:', w3.is_connected())
if w3.is_connected():
    print('Chain ID:', w3.eth.chain_id)
    print('Accounts:', w3.eth.accounts)
    print('Latest block:', w3.eth.block_number)
PY

You should see a successful connection, chain ID 1234, at least one account, and a changing/latest block number if the signer is producing blocks.

11. Compile and Deploy the Smart Contract
The active contract is:
ResourceAuction.sol

The repository is designed around a Remix → ABI/bytecode → Python deployment workflow.
Option A — Recommended: Compile in Remix, deploy from Python
11.1 Open Remix IDE
Open:
https://remix.ethereum.org/

Create ResourceAuction.sol and paste the repository contract.
11.2 Compile
Select a Solidity compiler compatible with:
pragma solidity ^0.8.0;

Compile the contract and obtain:
·	ABI
·	deployment bytecode
11.3 Deploy from the Raspberry Pi
The repository contains deploy.py and manual_deploy.py for the manual ABI/bytecode workflow.
Update the ABI/bytecode placeholders as required, then run:
python deploy.py

or:
python manual_deploy.py

Record the printed contract address.
11.4 Update the contract address in the gateway/tools
The address is currently hard-coded in several scripts. Replace it with the address from the current deployment in:
final_serial.py
check_data.py
data_export.py
find_esp32.py

For a cleaner production design, move the contract address and RPC URL into environment variables instead of hard-coding them.

Option B — Deploy directly from Remix
This is possible only when Remix can reach the private RPC endpoint and the RPC interface is configured appropriately.
For a Raspberry Pi on a LAN, exposing 8545 beyond loopback should be treated as a deliberate security change. Do not expose an unlocked signing RPC to the public internet.
For a local lab, the safer workflow is usually:
Remix → compile → copy ABI/bytecode → Python deploy script on Pi → local Geth RPC

12. Start the Edge Gateway
The primary runtime program in the repository is:
final_serial.py

Run:
source .venv/bin/activate
python final_serial.py

The program starts two services inside one Python process:
1.	a background serial listener for the Arduino
2.	a Flask server for ESP32 motion events
Expected runtime configuration:
Geth RPC        : 127.0.0.1:8545
Arduino serial  : /dev/ttyACM0
Arduino baud    : 115200
Flask API       : 0.0.0.0:5000

If your Arduino appears as /dev/ttyUSB0 instead, update the serial path in final_serial.py.

13. Arduino + DHT Sensor Path
The current Python listener expects the Arduino to emit text over serial.
A compatible example is:
TEMP:25.5,HUM:60.2

The listener looks for the substring TEMP:
if "TEMP" in line.upper():
    tx = contract.functions.requestResource("ARDUINO_DHT", 1).transact()

Therefore, the current behavior is:
Arduino line contains TEMP
        ↓
Raspberry Pi detects DHT event
        ↓
Blockchain transaction
        ↓
Sensor = ARDUINO_DHT
Priority = 1
Allocated = true

Important limitation
The current gateway does not place the actual temperature or humidity value on-chain. For example, the blockchain stores the event label ARDUINO_DHT, not 25.5 °C and 60.2 %.
To make the ledger store actual measurements, the smart contract would need additional fields such as:
int256 temperature;
uint256 humidity;
uint256 timestamp;

or a more scalable design where the raw measurement remains off-chain and only a cryptographic hash/reference is committed on-chain.

14. ESP32 + PIR Sensor Path
The Flask gateway exposes:
POST /motion

on port 5000.
The current Python implementation treats an incoming motion request as:
contract.functions.requestResource("ESP32_PIR", 2).transact()

A minimal test from another machine on the same LAN is:
curl -X POST http://<RASPBERRY_PI_IP>:5000/motion \
  -H 'Content-Type: application/json' \
  -d '{"event":"motion"}'

A successful response is similar to:
{
  "status": "Sent",
  "tx": "0x..."
}

The ESP32 firmware itself is not included in the repository snapshot, so the ESP32 side must be programmed separately to detect PIR state and send the HTTP request.

15. Auditing the Blockchain Ledger
15.1 Inspect recent records
Run:
python check_data.py

The script reads the contract's requestCount and prints recent entries.
You should see records resembling:
ID: 87  | [LOG] Sensor: ARDUINO_DHT | Priority: 1 | Status: Allocated
ID: 88  | [ALERT] Sensor: ESP32_PIR   | Priority: 2 | Status: Allocated

15.2 Search for PIR events
python find_esp32.py

The script scans ledger records and prints entries whose sensor name contains ESP32.
15.3 Export to CSV
python data_export.py

This produces:
blockchain_data.csv

with columns:
ID,Sensor,Priority,Status


16. Ledger Indexing Caveat in the Current Scripts
The Solidity contract increments requestCount before writing the mapping entry:
requestCount++;
requests[requestCount] = ...;

Therefore valid stored records begin at request ID 1.
Several helper scripts iterate from 0, which causes entry 0 to appear as the mapping's default empty record. The current CSV sample therefore contains an initial blank row.
For exact exports, an improved loop should use:
for i in range(1, count + 1):
    data = contract.functions.requests(i).call()
    # export data

The same indexing correction should be applied to auditing/search scripts if you want to inspect every record, including the newest record at requestCount.

17. Security Architecture
The blockchain portion contributes integrity and auditability rather than automatically securing every layer of the IoT system.
flowchart TB
    SENSOR[Sensor Event]
    VALIDATE[Edge Gateway\nReceive / Parse]
    AUTH[Authentication / Validation\nCurrent project: limited]
    TX[Signed Blockchain Transaction]
    BLOCK[Private Blockchain Block]
    AUDIT[Audit / Verification]

    SENSOR --> VALIDATE --> AUTH --> TX --> BLOCK --> AUDIT

What the current system protects well
·	Sensor event history is recorded on a blockchain instead of only in a local mutable file.
·	Transactions are associated with an Ethereum account through msg.sender.
·	The private chain uses permissioned block production in the original design.
·	A contract event provides a machine-readable audit signal.
What is not fully secured by the current code
·	The Flask /motion endpoint has no authentication. A reachable client could trigger a transaction.
·	The contract function requestResource() is public; there is no sender allow-list.
·	The DHT serial listener accepts any line containing TEMP; it does not validate the temperature/humidity values.
·	Raw sensor measurements are not stored on-chain.
·	The allocated flag is always set to true; there is no external resource scheduler in this repository.
·	No encryption is provided by the blockchain itself; blockchain data is visible to participants of the private network.
For a production-grade system, add device authentication, message integrity checks, authorization, replay protection, transport security, and a controlled key-management strategy.

18. Recommended Production-Grade Extension
A stronger version of the architecture can evolve into:
flowchart LR
    S[IoT Sensors]
    AUTH[Device Identity\nHMAC / mTLS / Signed Message]
    EDGE[Edge Gateway]
    RULES[Policy Engine\nPriority + Validation]
    DB[(Off-chain Time-Series Store)]
    HASH[Measurement Hash]
    BC[Permissioned Blockchain]
    UI[Audit Dashboard]

    S --> AUTH --> EDGE --> RULES
    RULES --> DB
    RULES --> HASH --> BC
    BC --> UI
    DB --> UI

This design keeps high-volume telemetry off-chain while committing a verifiable cryptographic fingerprint and critical security/resource events to the ledger.
Possible improvements include:
·	device-level identities instead of a shared gateway account
·	HMAC or digital signatures for sensor messages
·	authenticated Flask endpoints
·	input validation and replay protection
·	timestamped measurements
·	hash-based integrity commitments for raw telemetry
·	role-based smart-contract permissions
·	a real resource scheduler behind the allocated field
·	environment-based configuration for RPC URL and contract address
·	migration from deprecated Clique to a currently supported permissioned consensus technology

19. Troubleshooting
Failed to connect to Geth
Check that Geth is running and RPC is available:
curl -s -X POST http://127.0.0.1:8545 \
  -H 'Content-Type: application/json' \
  --data '{"jsonrpc":"2.0","method":"eth_blockNumber","params":[],"id":1}'

Also verify the Python endpoint is exactly:
http://127.0.0.1:8545

ExtraDataLengthError
The repository is using a PoA-compatible Web3 middleware:
w3.middleware_onion.inject(ExtraDataToPOAMiddleware, layer=0)

This is important for Geth-style PoA/dev chains.
Arduino is not detected
List serial devices:
ls /dev/ttyACM*
ls /dev/ttyUSB*

Then update:
serial.Serial('/dev/ttyACM0', 115200, timeout=1)

to the actual device path.
Permission denied on the serial port
On Raspberry Pi Linux, your user may need serial-device access. Check:
ls -l /dev/ttyACM0

Then add the user to the appropriate serial group if necessary and re-login.
Contract calls fail after redeployment
Every new deployment has a new contract address. Update the address in:
final_serial.py
check_data.py
data_export.py
find_esp32.py

Also ensure the ABI corresponds to the deployed ResourceAuction contract.
ESP32 POST succeeds but no blockchain entry appears
Check, in order:
1.	Flask is listening on port 5000.
2.	The Pi can reach Geth at 127.0.0.1:8545.
3.	The contract address is correct.
4.	The gateway account exists in Geth.
5.	The account can submit transactions.
6.	Geth is producing blocks.
7.	check_data.py is pointed at the same contract.

20. Example End-to-End Test
Terminal 1 — Geth
./bin/geth \
  --datadir runtime/node \
  --networkid 1234 \
  --http \
  --http.addr 127.0.0.1 \
  --http.port 8545 \
  --http.api eth,net,web3,personal,clique,txpool \
  --unlock 0xYOUR_SIGNER_ADDRESS \
  --password /secure/path/password.txt \
  --mine \
  --nodiscover \
  --maxpeers 0

Terminal 2 — Edge gateway
source .venv/bin/activate
python final_serial.py

Terminal 3 — Simulate PIR
curl -X POST http://127.0.0.1:5000/motion \
  -H 'Content-Type: application/json' \
  -d '{"event":"motion"}'

Terminal 4 — Verify the ledger
python check_data.py

Expected logical result:
Sensor     : ESP32_PIR
Priority   : 2
Status     : Allocated

Test the DHT path
Send a compatible test line to the Arduino/serial interface, for example:
TEMP:25.5,HUM:60.2

The gateway should create:
Sensor     : ARDUINO_DHT
Priority   : 1
Status     : Allocated

Again, the current contract records the event label and metadata, not the literal 25.5 / 60.2 measurement values.

21. Project Strengths
·	Edge-first design: sensor processing and blockchain interaction happen close to the devices.
·	Low-cost hardware: Raspberry Pi + commodity microcontrollers/sensors.
·	Auditable events: sensor/resource events become blockchain transactions.
·	Separation of concerns: sensors do not need blockchain libraries; the Pi acts as the gateway.
·	Priority-aware event model: routine and motion events use different priority levels.
·	Python-friendly integration: Flask, PySerial and Web3.py keep the gateway easy to inspect and extend.

22. Current Limitations
The current repository is best understood as a research/prototype implementation rather than a production-ready IoT security platform.
The major limitations are:
1.	raw measurements are not stored on-chain;
2.	device authentication is not implemented;
3.	/motion is unauthenticated;
4.	smart-contract authorization is open to public callers;
5.	allocated is a recorded state rather than a real resource scheduler;
6.	several helper scripts contain the older 0-based mapping scan;
7.	edge_gateway.py contains an older contract/API path and should not be treated as the canonical runtime;
8.	deploy_contract.py deploys a different ResourceBroker contract model from the active ResourceAuction.sol contract;
9.	the original chain setup relies on deprecated Clique-era infrastructure.
Documenting these boundaries makes the experiment easier to reproduce and prevents the README from claiming stronger guarantees than the implementation currently provides.

23. Research / Thesis Interpretation
The architecture can be summarized as:
Sensors generate events → the Raspberry Pi validates/mediates them → Web3.py submits signed transactions → Geth maintains the private ledger → Solidity records the event/resource state → audit tools reconstruct the history.
This makes the project relevant to Industrial IoT (IIoT), edge computing, blockchain-backed auditability, lightweight resource management and trusted sensor event logging.
The main engineering trade-off is that blockchain improves auditability and tamper resistance, while edge devices are constrained by CPU, memory, storage, network latency and key-management requirements. The gateway therefore becomes the critical integration point between lightweight sensing and the heavier trust mechanism.

24. License
No explicit license is included in the current project snapshot. Add a license file before treating the repository as a reusable open-source project.

Maintainer
Rosh-pvr / Roshan Sudhakar
GitHub: https://github.com/Rosh-pvr
Repository: https://github.com/Rosh-pvr/Rasberry_Blockchain

