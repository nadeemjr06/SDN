SDN-Based Network Utilization Monitor
Description

This project implements a Network Utilization Monitor using Software-Defined Networking (SDN). It uses the Ryu Controller to collect real-time network statistics from switches and analyze bandwidth usage and traffic flow.

The system provides centralized monitoring, making it easier to observe and manage network performance.

Features

Real-time network traffic monitoring
Bandwidth utilization calculation
Flow and port statistics collection
Centralized control using SDN
Simple and efficient implementation

Technologies Used

Python
Ryu Controller
Mininet
OpenFlow

System Architecture

Mininet creates a virtual network topology
Switches connect to the SDN controller
The controller sends requests for statistics
Switches respond with traffic data
The controller processes and displays network utilization

Installation and Setup

Prerequisites
Python installed
Mininet installed
Ryu Controller installed

Steps

Clone the repository:
git clone https://github.com/username/SDN.git
cd SDN
Run the Ryu controller:
ryu-manager monitor.py
Start Mininet topology:
sudo mn --topo single,3 --controller remote

How It Works

The controller periodically requests statistics from switches
Switches send flow and port data
The controller calculates bandwidth usage
Results are displayed in the terminal
Sample Output
Switch ID: 1
Port: 1 | TX Bytes: 2048 | RX Bytes: 1024
Bandwidth Usage: 1.5 Mbps

Use Cases

Network performance monitoring
Traffic analysis
Congestion detection
Learning SDN concepts
Real-time data visualization
Alert system for high traffic
Support for larger network topologies
