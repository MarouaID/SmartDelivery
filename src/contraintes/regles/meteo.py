from typing import List, Tuple
import random


class ValidateurMeteo:
 
    
    def __init__(self):
        self.conditions_acceptables = ['ensoleille', 'nuageux', 'pluie_legere']
        self.conditions_dangereuses = ['tempete', 'neige_forte', 'verglas']
    
    def obtenir_conditions_actuelles(self, latitude: float, 
                                    longitude: float) -> str:
        
        # Simulation aléatoire
        conditions_possibles = (self.conditions_acceptables + 
                               self.conditions_dangereuses)
        
        # 80% de chances d'avoir des conditions acceptables
        if random.random() < 0.8:
            return random.choice(self.conditions_acceptables)
        else:
            return random.choice(self.conditions_dangereuses)
    
    def valider_conditions(self, points_gps: List[Tuple[float, float]]) -> Tuple[bool, str]:
        
        if not points_gps:
            return True, ""
        
        conditions_problematiques = []
        
        for idx, (lat, lon) in enumerate(points_gps):
            condition = self.obtenir_conditions_actuelles(lat, lon)
            
            if condition in self.conditions_dangereuses:
                conditions_problematiques.append(
                    f"Point {idx}: {condition}"
                )
        
        if conditions_problematiques:
            message = ("Conditions météo dangereuses détectées:\n" + 
                      "\n".join(f"   • {c}" for c in conditions_problematiques))
            return False, message
        
        return True, "Conditions météo favorables"
    
    def calculer_facteur_ralentissement(self, condition: str) -> float:
        """
        Calcule le facteur de ralentissement dû à la météo
        
        Returns:
            Facteur multiplicateur (1.0 = normal, 1.5 = 50% plus lent)
        """
        facteurs = {
            'ensoleille': 1.0,
            'nuageux': 1.0,
            'pluie_legere': 1.2,
            'pluie_forte': 1.4,
            'tempete': 2.0,
            'neige_legere': 1.3,
            'neige_forte': 1.8,
            'verglas': 2.5
        }
        
        return facteurs.get(condition, 1.0)
