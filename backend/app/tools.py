# backend/app/tools.py

from .state_machine import StateMachine
from .rag import RAGSystem

class ToolRegistry:
    def __init__(self, session, rag: RAGSystem):
        self.session = session
        self.state_machine = StateMachine(session)
        self.rag = rag
    
    def look_up_artifact(self, item: str) -> str:
        current_room = self.session.get("current_location", "dive_boat")
        print(f"🔍 RAG Search: '{item}' at location: {current_room}")
        
        # Gear locker special case
        if "gear locker" in item.lower() and current_room == "dive_boat":
            if "depth_gauge_watch" not in self.session.get("inventory", []):
                self.state_machine.add_item("depth_gauge_watch")
                return "🔑 You open the gear locker and find a Depth-Gauge Watch! The Deep Outer Reef Wall is now unlocked!"
        
        # RAG search
        results = self.rag.search(item, current_room)
        
        if not results:
            return f"I don't have specific information about '{item}' at the {current_room}."
        
        return results[0] if isinstance(results, list) else str(results)
    
    def change_location(self, target_room: str) -> str:
        success, message = self.state_machine.move_to(target_room)
        return message
    
    def calculate_dive_limit(self, depth_m: float, tank_pressure_bar: int) -> str:
        if depth_m <= 0:
            return "❌ Please enter a valid depth greater than 0 meters."
        
        if tank_pressure_bar <= 0:
            return "❌ Please enter a valid tank pressure greater than 0 bar."
        
        base_time = 60.0 / (depth_m / 10 + 1)
        pressure_factor = tank_pressure_bar / 200.0
        adjusted_time = base_time * pressure_factor
        safe_time = max(5, min(60, adjusted_time))
        
        if depth_m > 30:
            safety = "⚠️ WARNING: This is a deep dive! Consider it a technical dive."
        elif depth_m > 20:
            safety = "⚠️ This is a deep recreational dive. Monitor your air carefully."
        else:
            safety = "✅ This is a safe recreational dive."
        
        return f"""
📊 **Dive Limit Calculation:**
• Depth: {depth_m}m
• Tank Pressure: {tank_pressure_bar} bar
• Safe Bottom Time: {int(safe_time)} minutes
{safety}
"""