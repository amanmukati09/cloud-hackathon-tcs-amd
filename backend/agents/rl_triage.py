"""
Reinforcement Learning Incident Triage Agent
Uses Q-Learning to learn optimal incident prioritization.
State: severity + component + hour + open_incidents
Action: priority level (1-5)
Reward: +10 for resolving critical fast, -5 for missing critical
"""

import numpy as np
import pickle
import os
from collections import defaultdict
from datetime import datetime

class RLTriageAgent:
    def __init__(self):
        self.q_table = defaultdict(lambda: np.zeros(5))  # 5 priority levels
        self.learning_rate = 0.1
        self.discount_factor = 0.95
        self.epsilon = 0.2  # exploration rate
        self.model_path = "rl_triage_model.pkl"
        self.load_model()
        
        # Severity mapping
        self.severity_map = {"CRITICAL": 4, "HIGH": 3, "MEDIUM": 2, "LOW": 1, "UNKNOWN": 0}
        self.component_map = {"Database": 0, "Nginx": 1, "Redis": 2, "API Gateway": 3, 
                              "System": 4, "Auth": 5, "Payment": 6, "Other": 7}
    
    def _get_state(self, incident: dict, open_count: int) -> tuple:
        """Convert incident to discrete state."""
        sev = self.severity_map.get(incident.get("severity", "MEDIUM"), 2)
        comp = self.component_map.get(incident.get("component", "Other"), 7)
        hour = datetime.now().hour // 4  # 0-5 (4-hour buckets)
        load = min(open_count // 5, 4)  # 0-4 workload buckets
        return (sev, comp, hour, load)
    
    def prioritize(self, incident: dict, open_count: int) -> dict:
        
        state = self._get_state(incident, open_count)
        
        if state in self.q_table and sum(abs(self.q_table[state])) > 0:
            if np.random.random() < self.epsilon:
                action = np.random.randint(0, 5)
            else:
                action = int(np.argmax(self.q_table[state]))
        else:
            sev = self.severity_map.get(incident.get("severity", "MEDIUM"), 2)
            action = min(sev, 4)
        
        priority = int(action + 1)
        
        # Convert numpy values to Python native types
        q_vals = [float(v) for v in self.q_table[state]]
        max_q = float(np.max(self.q_table[state])) if state in self.q_table else 0.0
        sum_q = float(sum(abs(self.q_table[state]))) if state in self.q_table else 1.0
        
        return {
            "incident_id": incident.get("id"),
            "priority": priority,
            "state": tuple(int(s) for s in state),
            "q_values": q_vals,
            "policy": "rule-based" if state not in self.q_table else ("explore" if np.random.random() < self.epsilon else "exploit"),
            "confidence": round(max_q / max(sum_q, 1) * 100, 1)
        }
    
    def learn(self, incident: dict, open_count: int, resolution_time_hours: float):
        """
        Update Q-table based on resolution outcome.
        Reward: faster resolution of critical = higher reward.
        """
        state = self._get_state(incident, open_count)
        sev = self.severity_map.get(incident.get("severity", "MEDIUM"), 2)
        
        # Calculate reward
        if resolution_time_hours < 1:
            reward = 10 * sev  # Fast resolution of critical = big reward
        elif resolution_time_hours < 4:
            reward = 5 * sev
        elif resolution_time_hours < 24:
            reward = 2 * sev
        else:
            reward = -5  # Penalty for slow resolution
        
        # Q-learning update
        action = np.argmax(self.q_table[state])
        old_value = self.q_table[state][action]
        next_max = np.max(self.q_table[state])
        
        new_value = old_value + self.learning_rate * (reward + self.discount_factor * next_max - old_value)
        self.q_table[state][action] = new_value
    
    def train_on_history(self, incidents: list):
        """Train the RL agent on historical incident data."""
        for inc in incidents:
            resolution_hours = inc.get("resolution_hours", 24)
            if resolution_hours and resolution_hours > 0:
                self.learn(inc, len(incidents), resolution_hours)
        self.save_model()
        return {"message": f"Trained on {len(incidents)} incidents", "q_table_size": len(self.q_table)}
    
    def get_priority_queue(self, incidents: list) -> list:
        """Sort incidents by RL-predicted priority."""
        open_count = sum(1 for i in incidents if i.get("status") == "open")
        prioritized = []
        for inc in incidents:
            result = self.prioritize(inc, open_count)
            prioritized.append({**inc, **result})
        
        # Sort by priority (highest first)
        prioritized.sort(key=lambda x: x["priority"], reverse=True)
        return prioritized
    
    def save_model(self):
        with open(self.model_path, "wb") as f:
            pickle.dump(dict(self.q_table), f)
    
    def load_model(self):
        if os.path.exists(self.model_path):
            with open(self.model_path, "rb") as f:
                self.q_table = defaultdict(lambda: np.zeros(5), pickle.load(f))


rl_agent = RLTriageAgent()