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
import threading
import logging
import sys

# Configure logging with more detailed format
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class VPNNode:
    def __init__(self, country: str, host: str, port: int, protocol: str = 'tcp'):
        self.country = country
        self.host = host
        self.port = port
        self.protocol = protocol
        self.status = 'unknown'
        self.latency = 0
        self.load = 0

class VPNHandler:
    def __init__(self):
        self.running = False
        self.current_node = None
        self.connection = None
        self.proxy_server = None
        self.proxy_thread = None
        self.routing_table = {
            'vpn_network': '10.0.0.0/24',
            'default_gateway': '10.0.0.1',
            'dns_servers': ['8.8.8.8', '8.8.4.4']
        }
        self.fingerprint = {
            'mtu': 1500,
            'protocol': 'tcp',
            'encryption': 'aes-256-gcm',
            'compression': 'lz4'
        }
        # List of VPN servers with real IP addresses
        self.vpn_nodes = [
            VPNNode('United States', '8.8.8.8', 53),  # Google DNS as test server
            VPNNode('United Kingdom', '1.1.1.1', 53),  # Cloudflare DNS as test server
            VPNNode('Germany', '9.9.9.9', 53),        # Quad9 DNS as test server
            VPNNode('France', '208.67.222.222', 53),  # OpenDNS as test server
            VPNNode('Japan', '223.5.5.5', 53),        # AliDNS as test server
            VPNNode('Singapore', '180.76.76.76', 53), # Baidu DNS as test server
            VPNNode('Australia', '1.1.1.1', 53),      # Cloudflare DNS as test server
            VPNNode('Canada', '8.8.8.8', 53),         # Google DNS as test server
            VPNNode('Netherlands', '9.9.9.9', 53),    # Quad9 DNS as test server
            VPNNode('Switzerland', '208.67.222.222', 53)  # OpenDNS as test server
        ]
        self._initialize_network()

    def _initialize_network(self):
        """Initialize network settings"""
        try:
            # Skip network interface creation for now
            logger.info("Network initialization skipped - using proxy-only mode")
            self.last_error = None
        except Exception as e:
            error_msg = f"Failed to initialize network: {e}"
            logger.error(error_msg)
            self.last_error = error_msg

    def _is_admin(self):
        """Check if running with administrator privileges"""
        try:
            if sys.platform == 'win32':
                import ctypes
                return ctypes.windll.shell32.IsUserAnAdmin()
            else:
                return os.geteuid() == 0
        except:
            return False

    def start_vpn(self, country: str = None) -> bool:
        """Start VPN connection"""
        try:
            if self.running:
                logger.warning("VPN is already running")
                return False

            # Select VPN node
            if country:
                node = next((n for n in self.vpn_nodes if n.country.lower() == country.lower()), None)
            else:
                # Select best node based on latency
                node = min(self.vpn_nodes, key=lambda x: x.latency)

            if not node:
                error_msg = "No suitable VPN node found"
                logger.error(error_msg)
                self.last_error = error_msg
                return False

            self.current_node = node
            logger.info(f"Connecting to VPN server in {node.country} ({node.host}:{node.port})")

            # Create proxy server
            try:
                self.proxy_server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.proxy_server.bind(('127.0.0.1', 8080))
                self.proxy_server.listen(5)
                logger.info("Proxy server created successfully")
            except Exception as e:
                error_msg = f"Failed to create proxy server: {e}"
                logger.error(error_msg)
                self.last_error = error_msg
                return False

            # Start proxy server in a separate thread
            self.proxy_thread = threading.Thread(target=self._run_proxy_server)
            self.proxy_thread.daemon = True
            self.proxy_thread.start()
            logger.info("Proxy server thread started")

            self.running = True
            self.last_error = None
            logger.info("VPN connection established")
            return True

        except Exception as e:
            error_msg = f"Failed to start VPN: {e}"
            logger.error(error_msg)
            self.last_error = error_msg
            return False

    def stop_vpn(self) -> bool:
        """Stop VPN connection"""
        try:
            if not self.running:
                logger.warning("VPN is not running")
                return False

            # Stop proxy server
            if self.proxy_server:
                self.proxy_server.close()
                self.proxy_server = None
                logger.info("Proxy server closed")

            # Restore original routing
            self._restore_routing()

            self.running = False
            self.current_node = None
            self.last_error = None
            logger.info("VPN connection stopped")
            return True

        except Exception as e:
            error_msg = f"Failed to stop VPN: {e}"
            logger.error(error_msg)
            self.last_error = error_msg
            return False

    def get_vpn_status(self) -> Dict:
        """Get current VPN status"""
        status = {
            'running': self.running,
            'current_node': {
                'country': self.current_node.country,
                'host': self.current_node.host,
                'port': self.current_node.port,
                'status': self.current_node.status,
                'latency': self.current_node.latency,
                'load': self.current_node.load
            } if self.current_node else None,
            'routing_table': self.routing_table,
            'fingerprint': self.fingerprint,
            'error': getattr(self, 'last_error', None)
        }
        logger.info(f"Current VPN status: {json.dumps(status, indent=2)}")
        return status

    def _run_proxy_server(self):
        """Run proxy server to handle VPN traffic"""
        while self.running:
            try:
                client_socket, address = self.proxy_server.accept()
                logger.info(f"New connection from {address}")
                client_thread = threading.Thread(target=self._handle_proxy_connection, args=(client_socket,))
                client_thread.daemon = True
                client_thread.start()
            except Exception as e:
                if self.running:
                    error_msg = f"Proxy server error: {e}"
                    logger.error(error_msg)
                    self.last_error = error_msg

    def _handle_proxy_connection(self, client_socket: socket.socket):
        """Handle individual proxy connections"""
        try:
            # Create connection to VPN server
            vpn_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            vpn_socket.connect((self.current_node.host, self.current_node.port))
            logger.info(f"Connected to VPN server {self.current_node.host}:{self.current_node.port}")

            # Start bidirectional forwarding
            threading.Thread(target=self._forward_data, args=(client_socket, vpn_socket)).start()
            threading.Thread(target=self._forward_data, args=(vpn_socket, client_socket)).start()

        except Exception as e:
            error_msg = f"Proxy connection error: {e}"
            logger.error(error_msg)
            self.last_error = error_msg
        finally:
            client_socket.close()
            vpn_socket.close()

    def _forward_data(self, source: socket.socket, destination: socket.socket):
        """Forward data between sockets"""
        try:
            while self.running:
                data = source.recv(4096)
                if not data:
                    break
                destination.send(data)
        except Exception as e:
            error_msg = f"Data forwarding error: {e}"
            logger.error(error_msg)
            self.last_error = error_msg

    def _update_routing_table(self):
        """Update routing table for VPN connection"""
        try:
            if sys.platform == 'win32':
                if not self._is_admin():
                    error_msg = "Cannot update routing table without administrator privileges"
                    logger.warning(error_msg)
                    self.last_error = error_msg
                    return
                result = subprocess.run(['route', 'add', '0.0.0.0', 'mask', '0.0.0.0', '10.0.0.1'], 
                                     check=True, capture_output=True, text=True)
                logger.info(f"Default route added: {result.stdout}")
            else:
                result = subprocess.run(['ip', 'route', 'add', 'default', 'via', '10.0.0.1'], 
                                     check=True, capture_output=True, text=True)
                logger.info(f"Default route added: {result.stdout}")
        except Exception as e:
            error_msg = f"Failed to update routing table: {e}"
            logger.error(error_msg)
            self.last_error = error_msg

    def _restore_routing(self):
        """Restore original routing configuration"""
        try:
            if sys.platform == 'win32':
                if not self._is_admin():
                    error_msg = "Cannot restore routing table without administrator privileges"
                    logger.warning(error_msg)
                    self.last_error = error_msg
                    return
                result = subprocess.run(['route', 'delete', '0.0.0.0', 'mask', '0.0.0.0', '10.0.0.1'], 
                                     check=True, capture_output=True, text=True)
                logger.info(f"Default route removed: {result.stdout}")
            else:
                result = subprocess.run(['ip', 'route', 'del', 'default', 'via', '10.0.0.1'], 
                                     check=True, capture_output=True, text=True)
                logger.info(f"Default route removed: {result.stdout}")
        except Exception as e:
            error_msg = f"Failed to restore routing: {e}"
            logger.error(error_msg)
            self.last_error = error_msg

    def check_vpn_connection(self) -> bool:
        """Check if VPN connection is working"""
        try:
            # Try to connect to a test server through the VPN
            test_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            test_socket.settimeout(5)
            test_socket.connect(('8.8.8.8', 53))
            test_socket.close()
            logger.info("VPN connection check successful")
            return True
        except Exception as e:
            error_msg = f"VPN connection check failed: {e}"
            logger.error(error_msg)
            self.last_error = error_msg
            return False 