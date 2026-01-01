// ============================================================
//               CONFIGURATION API
// ============================================================

const API_BASE_URL = '/api';

// ============================================================
//                UTILITAIRES GENERAUX
// ============================================================

const Utils = {

    async fetchAPI(endpoint, options = {}) {
        try {
            const response = await fetch(`${API_BASE_URL}${endpoint}`, {
                headers: {
                    'Content-Type': 'application/json',
                    ...options.headers
                },
                ...options
            });

            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }

            return await response.json();

        } catch (error) {
            console.error('Erreur API:', error);
            this.showNotification("Erreur de connexion à l'API", 'error');
            throw error;
        }
    },

    showNotification(message, type = 'info') {
        const notification = document.createElement('div');
        notification.className = `notification notification-${type}`;
        notification.textContent = message;

        notification.style.cssText = `
            position: fixed;
            top: 80px;
            right: 20px;
            padding: 15px 25px;
            background: ${type === 'error' ? '#f44336' : type === 'success' ? '#4caf50' : '#2196f3'};
            color: white;
            border-radius: 8px;
            box-shadow: 0 4px 15px rgba(0,0,0,0.2);
            z-index: 10000;
            animation: slideIn 0.3s ease;
        `;

        document.body.appendChild(notification);

        setTimeout(() => {
            notification.style.animation = 'slideOut 0.3s ease';
            setTimeout(() => notification.remove(), 300);
        }, 3000);
    }
};

// ============================================================
//                   SERVICE DE DONNEES
// ============================================================

const DataService = {

    async optimiser(params) {
        return await Utils.fetchAPI('/optimiser', {
            method: 'POST',
            body: JSON.stringify(params)
        });
    },

    async optimiserBnb(params) {
        // 🔥 Maintenant /optimiser et /optimiserBnb sont identiques
        return await Utils.fetchAPI('/optimiser', {
            method: 'POST',
            body: JSON.stringify(params)
        });
    }
};

// ============================================================
//            EXPORT GLOBAL
// ============================================================

window.SmartDelivery = {
    Utils,
    DataService
};
