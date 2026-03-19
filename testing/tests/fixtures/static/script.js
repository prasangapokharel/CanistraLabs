// ICP Test Project JavaScript

document.addEventListener('DOMContentLoaded', () => {
    // Set deployment date
    const deploymentDate = new Date().toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'long',
        day: 'numeric'
    });
    document.getElementById('deploymentDate').textContent = deploymentDate;

    // Add click handler to button
    const greetBtn = document.getElementById('greetBtn');
    const responseDiv = document.getElementById('response');

    greetBtn.addEventListener('click', async () => {
        greetBtn.disabled = true;
        greetBtn.innerHTML = '<span class="loading"></span> Processing...';
        
        try {
            // Simulate canister call
            const response = await simulateCanisterCall();
            
            responseDiv.innerHTML = `
                <strong>Canister Response:</strong>
                <p>${response.message}</p>
                <p><small>Timestamp: ${response.timestamp}</small></p>
            `;
            responseDiv.classList.add('show');
        } catch (error) {
            responseDiv.innerHTML = `<strong>Error:</strong> ${error.message}`;
            responseDiv.classList.add('show');
        } finally {
            greetBtn.disabled = false;
            greetBtn.textContent = 'Click Me';
        }
    });
});

/**
 * Simulate a canister call to the ICP
 * In a real application, this would call actual canister methods
 */
async function simulateCanisterCall() {
    return new Promise((resolve) => {
        setTimeout(() => {
            const messages = [
                'Hello from the Internet Computer! 🎉',
                'Successfully called canister method! ⚡',
                'ICP is live and responsive! 🌍',
                'Decentralized application working perfectly! 🔒'
            ];
            
            const randomMessage = messages[Math.floor(Math.random() * messages.length)];
            
            resolve({
                message: randomMessage,
                timestamp: new Date().toLocaleTimeString(),
                success: true
            });
        }, 800);
    });
}

/**
 * Real canister call handler (for actual ICP integration)
 */
async function callCanister(methodName, args = []) {
    try {
        // In production, this would call actual canister using @dfinity/agent
        const response = await fetch(`/canister/${methodName}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ args })
        });
        
        if (!response.ok) {
            throw new Error(`Canister call failed: ${response.statusText}`);
        }
        
        return await response.json();
    } catch (error) {
        console.error('Canister call error:', error);
        throw error;
    }
}

/**
 * Update UI with canister status
 */
async function updateCanisterStatus(canisterId) {
    try {
        const response = await fetch(`/api/v1/deployments/canisters/${canisterId}/status`, {
            headers: {
                'Authorization': `Bearer ${getStoredToken()}`
            }
        });
        
        if (response.ok) {
            const status = await response.json();
            console.log('Canister status:', status);
            return status;
        }
    } catch (error) {
        console.error('Failed to get canister status:', error);
    }
}

/**
 * Retrieve stored JWT token from localStorage
 */
function getStoredToken() {
    return localStorage.getItem('access_token') || '';
}

/**
 * Log page information for debugging
 */
function logPageInfo() {
    console.log('=== ICP Test Project Info ===');
    console.log('URL:', window.location.href);
    console.log('Timestamp:', new Date().toISOString());
    console.log('User Agent:', navigator.userAgent);
}

// Log page info on load
logPageInfo();
