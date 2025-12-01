// Configuration API
const API_BASE_URL = '/api';

// Utilitaires
const Utils = {
    /**
     * Effectue une requête fetch avec gestion d'erreurs
     */
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
            this.showNotification('Erreur de connexion à l\'API', 'error');
            throw error;
        }
    },

    /**
     * Affiche une notification toast
     */
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
    },

    /**
     * Formate une date ISO en format lisible
     */
    formatDate(isoString) {
        const date = new Date(isoString);
        return date.toLocaleString('fr-FR');
    },

    /**
     * Formate un nombre avec 2 décimales
     */
    formatNumber(num, decimals = 2) {
        return parseFloat(num).toFixed(decimals);
    },

    /**
     * Débounce une fonction
     */
    debounce(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    }
};

// Service de données
const DataService = {
    /**
     * Récupère les statistiques
     */
    async getStatistiques() {
        return await Utils.fetchAPI('/statistiques');
    },

    /**
     * Récupère tous les livreurs
     */
    async getLivreurs() {
        return await Utils.fetchAPI('/livreurs');
    },

    /**
     * Récupère un livreur par ID
     */
    async getLivreur(id) {
        return await Utils.fetchAPI(`/livreurs/${id}`);
    },

    /**
     * Récupère toutes les commandes
     */
    async getCommandes(filters = {}) {
        const params = new URLSearchParams(filters);
        return await Utils.fetchAPI(`/commandes?${params}`);
    },

    /**
     * Récupère une commande par ID
     */
    async getCommande(id) {
        return await Utils.fetchAPI(`/commandes/${id}`);
    },

    /**
     * Récupère tous les trajets
     */
    async getTrajets() {
        return await Utils.fetchAPI('/trajets');
    },

    /**
     * Récupère un trajet par ID livreur
     */
    async getTrajet(livreurId) {
        return await Utils.fetchAPI(`/trajets/${livreurId}`);
    },

    /**
     * Lance une optimisation
     */
    async optimiser(params) {
        return await Utils.fetchAPI('/optimiser', {
            method: 'POST',
            body: JSON.stringify(params)
        });
    },

    /**
     * Récupère les notifications
     */
    async getNotifications(utilisateurId) {
        return await Utils.fetchAPI(`/notifications?utilisateur_id=${utilisateurId}`);
    }
};

// Gestionnaire de WebSocket (simulé)
const WebSocketManager = {
    connected: false,
    callbacks: {},

    connect() {
        console.log('📡 Connexion WebSocket simulée');
        this.connected = true;
        
        // Simuler des mises à jour périodiques
        setInterval(() => {
            if (this.callbacks['position_update']) {
                // this.callbacks['position_update'](mockData);
            }
        }, 5000);
    },

    on(event, callback) {
        this.callbacks[event] = callback;
    },

    emit(event, data) {
        console.log(`📤 Émission: ${event}`, data);
    }
};

// Export global
window.SmartDelivery = {
    Utils,
    DataService,
    WebSocketManager
};

// Initialisation au chargement
document.addEventListener('DOMContentLoaded', () => {
    console.log('✅ Smart Delivery App chargée');
    
    // Ajouter les animations CSS
    const style = document.createElement('style');
    style.textContent = `
        @keyframes slideIn {
            from {
                transform: translateX(100%);
                opacity: 0;
            }
            to {
                transform: translateX(0);
                opacity: 1;
            }
        }
        
        @keyframes slideOut {
            from {
                transform: translateX(0);
                opacity: 1;
            }
            to {
                transform: translateX(100%);
                opacity: 0;
            }
        }
    `;
    document.head.appendChild(style);
});