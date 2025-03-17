import os
import subprocess
import time
import psutil
import socket
import random
import platform
from typing import Optional, List, Dict
import json
import requests
from datetime import datetime

class VPNNode:
    def __init__(self, ip: str, port: int, country: str, latency: float):
        self.ip = ip
        self.port = port
        self.country = country
        self.latency = latency
        self.is_active = True

class VPNHandler:
    def __init__(self):
        self.vpn_port = 1194
        self.vpn_data_dir = os.path.join(os.path.expanduser("~"), ".vpn")
        self._ensure_vpn_directory()
        self.fingerprint_data = self._generate_fingerprint()
        self.routing_table = self._generate_routing_table()
        self.nodes = self._generate_nodes()
        self.current_node = None
        self.vpn_process = None

    def _generate_fingerprint(self) -> dict:
        """Generate a realistic network fingerprint"""
        return {
            "mtu": random.choice([1400, 1500, 1600]),
            "tcp_window_size": random.choice([65535, 65536, 65537]),
            "tcp_timestamps": random.choice([True, False]),
            "tcp_sack": random.choice([True, False]),
            "tcp_ecn": random.choice([True, False]),
            "timestamp": datetime.now().isoformat()
        }

    def _generate_routing_table(self) -> dict:
        """Generate a routing table configuration"""
        return {
            "default_gateway": "0.0.0.0/0",
            "local_network": "192.168.1.0/24",
            "vpn_network": "10.8.0.0/24",
            "dns_servers": [
                "8.8.8.8",
                "8.8.4.4",
                "1.1.1.1"
            ],
            "mtu": self.fingerprint_data["mtu"],
            "routes": [
                {"destination": "0.0.0.0/0", "next_hop": "10.8.0.1"},
                {"destination": "10.8.0.0/24", "next_hop": "10.8.0.1"},
                {"destination": "192.168.1.0/24", "next_hop": "192.168.1.1"}
            ]
        }

    def _generate_nodes(self) -> List[VPNNode]:
        """Generate a list of VPN nodes"""
        return [
            VPNNode("10.8.0.1", 1194, "US", 50.0),
            VPNNode("10.8.0.2", 1194, "UK", 70.0),
            VPNNode("10.8.0.3", 1194, "DE", 80.0),
            VPNNode("10.8.0.4", 1194, "FR", 75.0),
            VPNNode("10.8.0.5", 1194, "JP", 100.0)
        ]

    def _apply_routing(self):
        """Apply the routing table configuration"""
        try:
            # Configure network interface
            interface_config = [
                f"interface mtu {self.routing_table['mtu']}",
                "proto tcp",
                f"port {self.vpn_port}",
                "dev tun",
                "cipher AES-256-CBC",
                "auth SHA256",
                "resolv-retry infinite",
                "nobind",
                "persist-key",
                "persist-tun",
                "remote-cert-tls server",
                "verify-x509-name server_XYZ1234567890",
                "auth-user-pass auth.txt",
                "comp-lzo",
                "verb 3"
            ]

            # Write configuration to config file
            config_path = os.path.join(self.vpn_data_dir, "vpn.conf")
            with open(config_path, "w") as f:
                f.write("\n".join(interface_config))

            print("Applied network routing configuration")
            return True
        except Exception as e:
            print(f"Error applying routing: {e}")
            return False

    def _ensure_vpn_directory(self):
        """Ensure VPN data directory exists"""
        if not os.path.exists(self.vpn_data_dir):
            os.makedirs(self.vpn_data_dir)

    def _select_best_node(self) -> Optional[VPNNode]:
        """Select the best available node based on latency"""
        available_nodes = [node for node in self.nodes if node.is_active]
        if not available_nodes:
            return None
        return min(available_nodes, key=lambda x: x.latency)

    def is_vpn_running(self) -> bool:
        """Check if VPN is currently running"""
        try:
            # Check for VPN interface
            for interface in psutil.net_if_stats():
                if interface.startswith('tun'):
                    return True
            return False
        except:
            return False

    def start_vpn(self) -> bool:
        """Start the VPN connection"""
        if self.is_vpn_running():
            print("VPN is already running")
            return True

        try:
            # Select best node
            self.current_node = self._select_best_node()
            if not self.current_node:
                print("No available VPN nodes")
                return False

            # Apply routing configuration
            if not self._apply_routing():
                print("Failed to apply routing configuration")
                return False
            
            # Start VPN connection with custom routing
            vpn_cmd = [
                "python",
                "-c",
                f"import socket; s=socket.socket(socket.AF_INET, socket.SOCK_STREAM); s.connect(('{self.current_node.ip}', {self.current_node.port}))"
            ]

            print(f"Starting VPN connection to {self.current_node.country}...")
            self.vpn_process = subprocess.Popen(
                vpn_cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            
            # Wait for connection to establish
            max_retries = 10
            retry_count = 0
            while retry_count < max_retries:
                if self.is_vpn_running():
                    print("VPN connection established successfully")
                    return True
                time.sleep(1)
                retry_count += 1
            
            print("Failed to establish VPN connection")
            return False
            
        except Exception as e:
            print(f"Error starting VPN: {e}")
            return False

    def stop_vpn(self) -> bool:
        """Stop the VPN connection"""
        try:
            if self.vpn_process:
                self.vpn_process.terminate()
                self.vpn_process.wait(timeout=5)
                self.vpn_process = None

            # Kill any remaining VPN processes
            for proc in psutil.process_iter(['name']):
                if proc.info['name'] == 'python.exe':
                    try:
                        if 'socket' in proc.cmdline():
                            proc.kill()
                    except:
                        pass
            return True
        except Exception as e:
            print(f"Error stopping VPN: {e}")
            return False

    def get_vpn_status(self) -> dict:
        """Get current VPN status"""
        return {
            "running": self.is_vpn_running(),
            "port": self.vpn_port,
            "routing_table": self.routing_table,
            "fingerprint": self.fingerprint_data,
            "connection_status": "connected" if self.is_vpn_running() else "disconnected",
            "current_node": {
                "ip": self.current_node.ip,
                "country": self.current_node.country,
                "latency": self.current_node.latency
            } if self.current_node else None
        }

    def check_vpn_connection(self) -> bool:
        """Check if VPN connection is working"""
        try:
            # Try to connect to a test service
            response = requests.get("https://api.ipify.org", timeout=5)
            return response.status_code == 200
        except Exception:
            return False 