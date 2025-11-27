"""
Fonctions utilitaires communes
"""

import json
import math
from datetime import datetime, timedelta
from typing import Tuple


class DistanceCalculator:
    """Calcul de distances géographiques"""
    
    EARTH_RADIUS_KM = 6371
    
    @staticmethod
    def haversine(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """
        Calcule la distance en km entre deux points GPS
        Formule de Haversine
        """
        lat1_rad = math.radians(lat1)
        lat2_rad = math.radians(lat2)
        delta_lat = math.radians(lat2 - lat1)
        delta_lon = math.radians(lon2 - lon1)
        
        a = (math.sin(delta_lat / 2) ** 2 +
             math.cos(lat1_rad) * math.cos(lat2_rad) *
             math.sin(delta_lon / 2) ** 2)
        
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        
        return DistanceCalculator.EARTH_RADIUS_KM * c
    
    @staticmethod
    def calculer_temps_trajet(distance_km: float, vitesse_kmh: float) -> int:
        """Retourne le temps en minutes"""
        if vitesse_kmh <= 0:
            return 0
        return int((distance_km / vitesse_kmh) * 60)


class TimeUtils:
    """Gestion des horaires"""
    
    @staticmethod
    def parse_time(time_str: str) -> datetime:
        """Convertit "HH:MM" en datetime"""
        return datetime.strptime(time_str, "%H:%M")
    
    @staticmethod
    def format_time(dt: datetime) -> str:
        """Convertit datetime en "HH:MM" """
        return dt.strftime("%H:%M")
    
    @staticmethod
    def add_minutes(time_str: str, minutes: int) -> str:
        """Ajoute des minutes à une heure"""
        dt = TimeUtils.parse_time(time_str)
        new_dt = dt + timedelta(minutes=minutes)
        return TimeUtils.format_time(new_dt)
    
    @staticmethod
    def is_in_window(time_str: str, window_start: str, window_end: str) -> bool:
        """Vérifie si l'heure est dans la fenêtre"""
        time = TimeUtils.parse_time(time_str)
        start = TimeUtils.parse_time(window_start)
        end = TimeUtils.parse_time(window_end)
        return start <= time <= end


class ConfigLoader:
    """Chargement de la configuration"""
    
    @staticmethod
    def load_config(filepath: str = "config/config.json") -> dict:
        """Charge le fichier de configuration"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            print(f"⚠️ Fichier {filepath} introuvable, utilisation config par défaut")
            return {}
    
    @staticmethod
    def save_config(config: dict, filepath: str = "config/config.json"):
        """Sauvegarde la configuration"""
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
