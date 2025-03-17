import os
import subprocess
import time
import psutil
import socket
import random
import platform
from typing import Optional
import json
import requests
from datetime import datetime

class VPNHandler:
    def __init__(self):
        self.vpn_port = 1194
        self.vpn_data_dir = os.path.join(os.path.expanduser("~"), ".vpn")
        self._ensure_vpn_directory()
        self.fingerprint_data = self._generate_fingerprint()
        self.routing_table = self._generate_routing_table()

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
            "mtu": self.fingerprint_data["mtu"]
        }

    def _apply_routing(self):
        """Apply the routing table configuration"""
        try:
            # Configure network interface
            interface_config = [
                f"interface mtu {self.routing_table['mtu']}",
                "proto udp",
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
            # Apply routing configuration
            self._apply_routing()
            
            # Start VPN connection
            vpn_cmd = [
                "openvpn",
                "--config", os.path.join(self.vpn_data_dir, "vpn.conf")
            ]

            print("Starting VPN connection...")
            subprocess.Popen(vpn_cmd)
            time.sleep(5)  # Wait for connection to establish
            
            return self.is_vpn_running()
        except Exception as e:
            print(f"Error starting VPN: {e}")
            return False

    def stop_vpn(self) -> bool:
        """Stop the VPN connection"""
        try:
            # Kill any running OpenVPN processes
            for proc in psutil.process_iter(['name']):
                if proc.info['name'] == 'openvpn.exe':
                    proc.kill()
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
            "fingerprint": self.fingerprint_data
        }

    def check_vpn_connection(self) -> bool:
        """Check if VPN connection is working"""
        try:
            # Try to connect to a test service
            response = requests.get("https://api.ipify.org", timeout=5)
            return response.status_code == 200
        except Exception:
            return False 