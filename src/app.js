class VPNClient {
    constructor() {
        this.isConnected = false;
        this.startTime = null;
        this.dataTransferred = 0;
        this.websocket = null;
        this.trafficInterval = null;
        this.connectionTimer = null;

        // DOM Elements
        this.connectBtn = document.getElementById('connectBtn');
        this.disconnectBtn = document.getElementById('disconnectBtn');
        this.serverAddress = document.getElementById('serverAddress');
        this.statusIndicator = document.getElementById('statusIndicator');
        this.statusArea = document.getElementById('statusArea');
        this.trafficBar = document.querySelector('.traffic-fill');
        this.trafficPercentage = document.getElementById('trafficPercentage');
        this.dataTransferredElement = document.getElementById('dataTransferred');
        this.connectionTimeElement = document.getElementById('connectionTime');
        this.currentSpeedElement = document.getElementById('currentSpeed');
        this.statusText = document.getElementById('statusText');
        this.mtuElement = document.getElementById('mtu');
        this.portElement = document.getElementById('port');
        this.networkElement = document.getElementById('network');
        this.countrySelect = document.getElementById('countrySelect');

        // Event Listeners
        this.connectBtn.addEventListener('click', () => this.connect());
        this.disconnectBtn.addEventListener('click', () => this.disconnect());
        this.countrySelect.addEventListener('change', () => this.handleCountryChange());
    }

    async connect() {
        try {
            const response = await fetch('/connect', { method: 'POST' });
            const success = await response.json();
            
            if (success) {
                await this.updateStatus();
            } else {
                alert('Failed to connect to VPN');
            }
        } catch (error) {
            console.error('Error connecting:', error);
            alert('Error connecting to VPN');
        }
    }

    async disconnect() {
        try {
            const response = await fetch('/disconnect', { method: 'POST' });
            const success = await response.json();
            
            if (success) {
                await this.updateStatus();
            } else {
                alert('Failed to disconnect from VPN');
            }
        } catch (error) {
            console.error('Error disconnecting:', error);
            alert('Error disconnecting from VPN');
        }
    }

    async updateStatus() {
        try {
            const response = await fetch('/status');
            const status = await response.json();
            
            this.isConnected = status.running;
            this.statusIndicator.classList.toggle('connected', this.isConnected);
            this.statusText.textContent = this.isConnected ? 'Connected' : 'Disconnected';
            
            this.connectBtn.disabled = this.isConnected;
            this.disconnectBtn.disabled = !this.isConnected;

            // Update connection info
            this.mtuElement.textContent = status.fingerprint.mtu;
            this.portElement.textContent = status.port;
            this.networkElement.textContent = status.routing_table.vpn_network;

            if (status.current_node) {
                this.countrySelect.value = status.current_node.country;
            }
        } catch (error) {
            console.error('Error updating status:', error);
        }
    }

    startMonitoring() {
        // Update traffic bar
        this.trafficInterval = setInterval(() => {
            const traffic = Math.random() * 100;
            this.trafficBar.style.width = `${traffic}%`;
            this.trafficPercentage.textContent = `${Math.round(traffic)}%`;
        }, 1000);

        // Update connection time
        this.connectionTimer = setInterval(() => {
            const elapsed = Date.now() - this.startTime;
            const hours = Math.floor(elapsed / 3600000);
            const minutes = Math.floor((elapsed % 3600000) / 60000);
            const seconds = Math.floor((elapsed % 60000) / 1000);
            this.connectionTimeElement.textContent = 
                `${hours.toString().padStart(2, '0')}:${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
        }, 1000);
    }

    stopMonitoring() {
        if (this.trafficInterval) {
            clearInterval(this.trafficInterval);
            this.trafficInterval = null;
        }
        if (this.connectionTimer) {
            clearInterval(this.connectionTimer);
            this.connectionTimer = null;
        }
        this.trafficBar.style.width = '0%';
        this.trafficPercentage.textContent = '0%';
    }

    handleServerMessage(data) {
        if (data.type === 'traffic') {
            this.dataTransferred += data.size;
            this.dataTransferredElement.textContent = `${(this.dataTransferred / 1024 / 1024).toFixed(2)} MB`;
            this.currentSpeedElement.textContent = `${(data.speed / 1024 / 1024).toFixed(2)} MB/s`;
        } else if (data.type === 'status') {
            this.logStatus(data.message);
        }
    }

    logStatus(message) {
        const timestamp = new Date().toLocaleTimeString();
        const logEntry = document.createElement('div');
        logEntry.textContent = `[${timestamp}] ${message}`;
        this.statusArea.appendChild(logEntry);
        this.statusArea.scrollTop = this.statusArea.scrollHeight;
    }

    handleCountryChange() {
        if (this.isConnected) {
            // If connected, disconnect first
            this.disconnect();
        }
    }
}

// Initialize the VPN client when the page loads
document.addEventListener('DOMContentLoaded', function() {
    const connectButton = document.getElementById('connectButton');
    const statusText = document.getElementById('statusText');
    const countrySelect = document.getElementById('countrySelect');
    let isConnected = false;

    // Populate country select with available servers
    function populateCountrySelect() {
        fetch('http://localhost:8000', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ action: 'status' })
        })
        .then(response => response.json())
        .then(data => {
            if (data.success && data.servers) {
                countrySelect.innerHTML = '';
                data.servers.forEach(server => {
                    const option = document.createElement('option');
                    option.value = server.country;
                    option.textContent = server.country;
                    countrySelect.appendChild(option);
                });
            }
        })
        .catch(error => {
            console.error('Error fetching servers:', error);
        });
    }

    // Update status periodically
    function updateStatus() {
        fetch('http://localhost:8000', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ action: 'status' })
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                const status = data.status;
                isConnected = status.running;
                statusText.textContent = isConnected ? 'Connected' : 'Disconnected';
                connectButton.textContent = isConnected ? 'Disconnect' : 'Connect';
                connectButton.className = isConnected ? 'btn btn-danger' : 'btn btn-success';
                
                if (status.current_node) {
                    countrySelect.value = status.current_node.country;
                }
            } else {
                statusText.textContent = 'Error';
                console.error('Status error:', data.error);
            }
        })
        .catch(error => {
            console.error('Error updating status:', error);
            statusText.textContent = 'Error';
        });
    }

    // Update status every 5 seconds
    setInterval(updateStatus, 5000);
    updateStatus(); // Initial status check
    populateCountrySelect(); // Populate country select

    connectButton.addEventListener('click', function() {
        const action = isConnected ? 'disconnect' : 'connect';
        const selectedCountry = countrySelect.value;
        
        fetch('http://localhost:8000', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ 
                action: action,
                country: selectedCountry
            })
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                isConnected = action === 'connect';
                statusText.textContent = isConnected ? 'Connected' : 'Disconnected';
                connectButton.textContent = isConnected ? 'Disconnect' : 'Connect';
                connectButton.className = isConnected ? 'btn btn-danger' : 'btn btn-success';
            } else {
                statusText.textContent = 'Connection failed';
                console.error('Connection error:', data.error);
            }
        })
        .catch(error => {
            console.error('Error:', error);
            statusText.textContent = 'Error';
        });
    });

    countrySelect.addEventListener('change', function() {
        if (isConnected) {
            // If connected, disconnect first
            connectButton.click();
        }
    });
}); 