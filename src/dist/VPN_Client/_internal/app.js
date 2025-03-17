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

        // Event Listeners
        this.connectBtn.addEventListener('click', () => this.connect());
        this.disconnectBtn.addEventListener('click', () => this.disconnect());
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
}

// Initialize the VPN client when the page loads
document.addEventListener('DOMContentLoaded', () => {
    const connectBtn = document.getElementById('connectBtn');
    const disconnectBtn = document.getElementById('disconnectBtn');
    const statusIndicator = document.getElementById('statusIndicator');
    const statusText = document.getElementById('statusText');
    const mtuElement = document.getElementById('mtu');
    const portElement = document.getElementById('port');
    const networkElement = document.getElementById('network');

    let isConnected = false;

    async function updateStatus() {
        try {
            const response = await fetch('/status');
            const status = await response.json();
            
            isConnected = status.running;
            statusIndicator.classList.toggle('connected', isConnected);
            statusText.textContent = isConnected ? 'Connected' : 'Disconnected';
            
            connectBtn.disabled = isConnected;
            disconnectBtn.disabled = !isConnected;

            // Update connection info
            mtuElement.textContent = status.fingerprint.mtu;
            portElement.textContent = status.port;
            networkElement.textContent = status.routing_table.vpn_network;
        } catch (error) {
            console.error('Error updating status:', error);
        }
    }

    async function connect() {
        try {
            const response = await fetch('/connect', { method: 'POST' });
            const success = await response.json();
            
            if (success) {
                await updateStatus();
            } else {
                alert('Failed to connect to VPN');
            }
        } catch (error) {
            console.error('Error connecting:', error);
            alert('Error connecting to VPN');
        }
    }

    async function disconnect() {
        try {
            const response = await fetch('/disconnect', { method: 'POST' });
            const success = await response.json();
            
            if (success) {
                await updateStatus();
            } else {
                alert('Failed to disconnect from VPN');
            }
        } catch (error) {
            console.error('Error disconnecting:', error);
            alert('Error disconnecting from VPN');
        }
    }

    connectBtn.addEventListener('click', connect);
    disconnectBtn.addEventListener('click', disconnect);

    // Update status every 5 seconds
    setInterval(updateStatus, 5000);
    // Initial status update
    updateStatus();
}); 