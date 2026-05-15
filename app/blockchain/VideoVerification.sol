// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

contract VideoVerification {
    mapping (string => bool) public verified;
    event Stored(string videoHash, address indexed who, uint256 timestamp);

    function storeHash(string memory videoHash) public {
        verified[videoHash] = true;
        emit Stored(videoHash, msg.sender, block.timestamp);
    }

    function verifyHash(string memory videoHash) public view returns (bool) {
        return verified[videoHash];
    }
}
