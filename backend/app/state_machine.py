# backend/app/state_machine.py

from typing import List, Optional, Dict

NAVIGATION_GRAPH = {
    "dive_boat": ["reef_flats"],
    "reef_flats": ["dive_boat", "reef_wall"],
    "reef_wall": ["reef_flats"]
}

LOCATIONS = {
    "dive_boat": {
        "name": "Expedition Dive Boat",
        "description": "You're on the expedition dive boat...",
        "background": "dive_boat.jpg"
    },
    "reef_flats": {
        "name": "Shallow Reef Flats",
        "description": "You're in the shallow reef flats...",
        "background": "reef_flats.jpg"
    },
    "reef_wall": {
        "name": "Deep Outer Reef Wall",
        "description": "You're at the deep outer reef wall...",
        "background": "reef_wall.jpg"
    }
}

LOCKS = {
    "reef_wall": {
        "requires": "depth_gauge_watch",
        "message": "The Deep Outer Reef Wall is locked! You need a Depth-Gauge Watch."
    }
}

class StateMachine:
    def __init__(self, session_data: Dict):
        self.session = session_data
    
    def get_current_location(self) -> str:
        return self.session.get("current_location", "dive_boat")
    
    def get_location_info(self, location: str) -> Dict:
        return LOCATIONS.get(location, LOCATIONS["dive_boat"])
    
    def get_valid_moves(self) -> List[str]:
        current = self.get_current_location()
        return NAVIGATION_GRAPH.get(current, [])
    
    def can_move_to(self, target: str) -> tuple[bool, str]:
        current = self.get_current_location()
        
        if current == target:
            return False, f"You are already at {LOCATIONS[target]['name']}."
        
        if target not in self.get_valid_moves():
            return False, f"Cannot go from {current} to {target}"
        
        if target in LOCKS:
            lock = LOCKS[target]
            if lock["requires"] not in self.session.get("inventory", []):
                return False, lock["message"]
        
        return True, "OK"
    
    def move_to(self, target: str) -> tuple[bool, str]:
        can_move, message = self.can_move_to(target)
        if not can_move:
            return False, message
        
        self.session["current_location"] = target
        return True, f"Moved to {LOCATIONS[target]['name']}"
    
    def add_item(self, item: str):
        if "inventory" not in self.session:
            self.session["inventory"] = []
        if item not in self.session["inventory"]:
            self.session["inventory"].append(item)
    
    def get_context_chips(self) -> List[str]:
        current = self.get_current_location()
        
        if current == "dive_boat":
            return [
                "⚓ Check Gear Locker",
                "🏝️ Go to Reef Flats",
                "☀️ Check Weather"
            ]
        elif current == "reef_flats":
            chips = ["🔍 Look for clownfish", "⛵ Go back to Dive Boat"]
            can_move, _ = self.can_move_to("reef_wall")
            if can_move:
                chips.append("🌊 Go to Deep Outer Reef Wall")
            else:
                chips.append("🔒 Deep Wall is locked")
            return chips
        elif current == "reef_wall":
            return [
                "🦈 Look for sharks",
                "⛵ Go back to Reef Flats",
                "🌊 Check dive conditions",
                "⏱️ Calculate my dive limit"
            ]
        return []