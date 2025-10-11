/**
 * Electron-Python Bridge Example - Simplified Implementation
 * Demonstrates JSON-RPC communication between Electron and Python backend
 *
 * Note: This is a simplified educational example created for demo purposes.
 */

const { spawn } = require('child_process');
const { EventEmitter } = require('events');

/**
 * JSON-RPC Bridge for Electron-Python communication
 * Demonstrates the communication protocol concepts
 */
class ElectronPythonBridge extends EventEmitter {
    constructor(pythonScriptPath, options = {}) {
        super();

        this.pythonProcess = null;
        this.scriptPath = pythonScriptPath;
        this.requestId = 0;
        this.pendingRequests = new Map();
        this.connected = false;

        // Configuration options
        this.options = {
            timeout: options.timeout || 30000,
            pythonExecutable: options.pythonExecutable || 'python',
            maxRetries: options.maxRetries || 3,
            ...options
        };
    }

    /**
     * Start the Python subprocess and establish communication
     */
    async connect() {
        return new Promise((resolve, reject) => {
            try {
                // Spawn Python process
                this.pythonProcess = spawn(this.options.pythonExecutable, [
                    this.scriptPath,
                    '--electron'  // Signal to Python that it's running in Electron mode
                ], {
                    stdio: ['pipe', 'pipe', 'pipe'],
                    shell: false
                });

                // Setup event handlers
                this.pythonProcess.stdout.on('data', (data) => {
                    this._handlePythonOutput(data);
                });

                this.pythonProcess.stderr.on('data', (data) => {
                    console.error('Python stderr:', data.toString());
                });

                this.pythonProcess.on('error', (error) => {
                    console.error('Python process error:', error);
                    this.emit('error', error);
                });

                this.pythonProcess.on('exit', (code) => {
                    console.log('Python process exited with code:', code);
                    this.connected = false;
                    this.emit('disconnected', code);
                });

                // Wait for ready signal
                this.once('ready', () => {
                    this.connected = true;
                    resolve();
                });

                // Timeout if no ready signal
                setTimeout(() => {
                    if (!this.connected) {
                        reject(new Error('Python backend connection timeout'));
                    }
                }, this.options.timeout);

            } catch (error) {
                reject(error);
            }
        });
    }

    /**
     * Send a JSON-RPC request to Python backend
     */
    async sendRequest(method, params = {}) {
        if (!this.connected) {
            throw new Error('Bridge not connected');
        }

        const requestId = ++this.requestId;
        const request = {
            jsonrpc: '2.0',
            id: requestId,
            method: method,
            params: params
        };

        return new Promise((resolve, reject) => {
            // Store pending request
            this.pendingRequests.set(requestId, {
                resolve,
                reject,
                timestamp: Date.now()
            });

            // Send request
            const requestData = JSON.stringify(request) + '\n';
            this.pythonProcess.stdin.write(requestData);

            // Setup timeout
            setTimeout(() => {
                if (this.pendingRequests.has(requestId)) {
                    this.pendingRequests.delete(requestId);
                    reject(new Error(`Request timeout: ${method}`));
                }
            }, this.options.timeout);
        });
    }

    /**
     * Handle output from Python process
     */
    _handlePythonOutput(data) {
        const lines = data.toString().split('\n').filter(line => line.trim());

        for (const line of lines) {
            try {
                const message = JSON.parse(line);
                this._processMessage(message);
            } catch (error) {
                console.warn('Failed to parse Python output:', line);
            }
        }
    }

    /**
     * Process a message from Python backend
     */
    _processMessage(message) {
        // Handle ready signal
        if (message.status === 'ready') {
            this.emit('ready');
            return;
        }

        // Handle JSON-RPC response
        if (message.jsonrpc === '2.0' && message.id) {
            const pendingRequest = this.pendingRequests.get(message.id);
            if (pendingRequest) {
                this.pendingRequests.delete(message.id);

                if (message.error) {
                    pendingRequest.reject(new Error(message.error.message));
                } else {
                    pendingRequest.resolve(message.result);
                }
            }
            return;
        }

        // Handle notifications
        if (message.method) {
            this.emit('notification', message.method, message.params);
        }
    }

    /**
     * Disconnect from Python backend
     */
    disconnect() {
        if (this.pythonProcess) {
            this.pythonProcess.kill();
            this.pythonProcess = null;
        }
        this.connected = false;
        this.pendingRequests.clear();
    }

    /**
     * Get current connection status
     */
    isConnected() {
        return this.connected;
    }
}

/**
 * High-level API wrapper for common operations
 */
class AIWindowManager {
    constructor(bridgePath) {
        this.bridge = new ElectronPythonBridge(bridgePath);
        this.activeApps = [];
        this.setupEventHandlers();
    }

    setupEventHandlers() {
        this.bridge.on('ready', () => {
            console.log('Python backend ready');
        });

        this.bridge.on('error', (error) => {
            console.error('Bridge error:', error);
        });

        this.bridge.on('notification', (method, params) => {
            console.log('Notification:', method, params);
        });
    }

    async connect() {
        await this.bridge.connect();
    }

    async disconnect() {
        this.bridge.disconnect();
    }

    /**
     * Get list of active AI applications
     */
    async getActiveApps() {
        try {
            const result = await this.bridge.sendRequest('get_active_apps');
            this.activeApps = result || [];
            return this.activeApps;
        } catch (error) {
            console.error('Failed to get active apps:', error);
            return [];
        }
    }

    /**
     * Arrange windows in grid layout
     */
    async arrangeWindows(layout = 'grid', options = {}) {
        try {
            const params = {
                layout: layout,
                ...options
            };

            const result = await this.bridge.sendRequest('arrange_windows', params);
            return result;
        } catch (error) {
            console.error('Failed to arrange windows:', error);
            throw error;
        }
    }

    /**
     * Start all configured AI applications
     */
    async startAllApps() {
        try {
            const result = await this.bridge.sendRequest('start_ai_apps');
            return result;
        } catch (error) {
            console.error('Failed to start apps:', error);
            throw error;
        }
    }

    /**
     * Close all AI applications
     */
    async closeAllApps() {
        try {
            const result = await this.bridge.sendRequest('close_all');
            return result;
        } catch (error) {
            console.error('Failed to close apps:', error);
            throw error;
        }
    }

    /**
     * Minimize all AI windows
     */
    async minimizeAllApps() {
        try {
            const result = await this.bridge.sendRequest('minimize_all');
            return result;
        } catch (error) {
            console.error('Failed to minimize apps:', error);
            throw error;
        }
    }

    /**
     * Restore all AI windows
     */
    async restoreAllApps() {
        try {
            const result = await this.bridge.sendRequest('restore_all');
            return result;
        } catch (error) {
            console.error('Failed to restore apps:', error);
            throw error;
        }
    }

    /**
     * Send prompt to selected AI applications
     */
    async sendPrompt(prompt, selectedApps = []) {
        try {
            const params = {
                prompt: prompt,
                selected_apps: selectedApps
            };

            const result = await this.bridge.sendRequest('send_prompt', params);
            return result;
        } catch (error) {
            console.error('Failed to send prompt:', error);
            throw error;
        }
    }

    /**
     * Get configuration from backend
     */
    async getConfig() {
        try {
            const result = await this.bridge.sendRequest('get_config');
            return result;
        } catch (error) {
            console.error('Failed to get config:', error);
            throw error;
        }
    }

    /**
     * Update configuration
     */
    async updateConfig(config) {
        try {
            const params = { config: config };
            const result = await this.bridge.sendRequest('update_config', params);
            return result;
        } catch (error) {
            console.error('Failed to update config:', error);
            throw error;
        }
    }
}

/**
 * Demo usage example
 */
async function demonstrateUsage() {
    console.log('AI Window Manager Demo');
    console.log('='.repeat(30));

    // Create window manager instance
    const windowManager = new AIWindowManager('./backend/main.py');

    try {
        // Connect to Python backend
        console.log('Connecting to Python backend...');
        await windowManager.connect();
        console.log('✓ Connected successfully');

        // Get configuration
        console.log('\nGetting configuration...');
        const config = await windowManager.getConfig();
        console.log('✓ Configuration loaded:', {
            aiApps: config.ai_apps?.length || 0,
            layoutMode: config.window?.layout_mode || 'unknown'
        });

        // Get active applications
        console.log('\nScanning for active AI applications...');
        const activeApps = await windowManager.getActiveApps();
        console.log(`✓ Found ${activeApps.length} active AI applications`);

        if (activeApps.length > 0) {
            // Arrange windows
            console.log('\nArranging windows in grid layout...');
            const arrangeResult = await windowManager.arrangeWindows('grid', {
                cols: 4,
                rows: 2
            });
            console.log('✓ Windows arranged:', arrangeResult);

            // Demonstrate prompt sending
            console.log('\nSending test prompt...');
            const promptResult = await windowManager.sendPrompt(
                'Hello, this is a test prompt from the demo.',
                activeApps.slice(0, 2).map(app => app.name)
            );
            console.log('✓ Prompt sent:', promptResult);
        }

    } catch (error) {
        console.error('Demo failed:', error.message);
    } finally {
        // Cleanup
        console.log('\nDisconnecting...');
        await windowManager.disconnect();
        console.log('✓ Disconnected');
    }
}

// Export classes for use in other modules
module.exports = {
    ElectronPythonBridge,
    AIWindowManager,
    demonstrateUsage
};

// Run demo if this file is executed directly
if (require.main === module) {
    demonstrateUsage().catch(console.error);
}