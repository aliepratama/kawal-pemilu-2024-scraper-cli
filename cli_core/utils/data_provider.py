"""Data provider for location data."""

import json
from typing import Dict, List, Tuple


class LocationDataProvider:
    """Provider for location data from context/tps.json."""
    
    def __init__(self, context_path: str):
        """
        Initialize data provider.
        
        Args:
            context_path: Path to tps.json file
        """
        self.context_path = context_path
        self._data = None
        self._id2name = None
        self._name2id = None
    
    def load_data(self):
        """Load data from context file."""
        if self._data is None:
            with open(self.context_path, 'r', encoding='utf-8') as f:
                self._data = json.load(f)
            self._id2name = self._data['id2name']
            self._name2id = self._data['name2id']
    
    @property
    def id2name(self) -> Dict[str, str]:
        """Get ID to name mapping."""
        if self._id2name is None:
            self.load_data()
        return self._id2name
    
    @property
    def name2id(self) -> Dict[str, str]:
        """Get name to ID mapping."""
        if self._name2id is None:
            self.load_data()
        return self._name2id
    
    def get_provinces(self) -> Dict[str, str]:
        """Get all provinces (2-digit IDs)."""
        return {k: v for k, v in self.id2name.items() if len(k) == 2}
    
    def get_regencies(self, province_id: str) -> Dict[str, str]:
        """Get all regencies in a province (4-digit IDs)."""
        return {k: v for k, v in self.id2name.items() 
                if len(k) == 4 and k.startswith(province_id)}
    
    def get_districts(self, regency_id: str) -> Dict[str, str]:
        """Get all districts in a regency (6-digit IDs)."""
        return {k: v for k, v in self.id2name.items() 
                if len(k) == 6 and k.startswith(regency_id)}
    
    def get_villages(self, district_id: str) -> Dict[str, str]:
        """Get all villages in a district (10-digit IDs)."""
        return {k: v for k, v in self.id2name.items() 
                if len(k) == 10 and k.startswith(district_id)}
    
    def get_all_villages_in_regency(self, regency_id: str) -> Dict[str, str]:
        """Get all villages in a regency."""
        return {k: v for k, v in self.id2name.items() 
                if len(k) == 10 and k.startswith(regency_id)}
