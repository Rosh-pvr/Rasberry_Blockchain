// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

contract ResourceAuction {
    address public edgeNode; // Your Raspberry Pi Address

    struct ResourceRequest {
        address requester;
        string sensorType;
        uint256 priority; // 1 = Routine, 2 = Critical (Motion)
        bool allocated;
    }

    mapping(uint256 => ResourceRequest) public requests;
    uint256 public requestCount;

    event ResourceAllocated(uint256 requestId, string sensor, uint256 priority);

    constructor() {
        edgeNode = msg.sender; // The Pi's address you just generated
    }

    // IoT nodes call this to offload a task
    function requestResource(string memory _sensor, uint256 _priority) public {
        requestCount++;
        requests[requestCount] = ResourceRequest(msg.sender, _sensor, _priority, true);
        
        // Automated logic: Immediate allocation for priority 2
        emit ResourceAllocated(requestCount, _sensor, _priority);
    }
}
