class GamificationEngine:
    """Awards points and badges for user actions."""
    
    # Points awarded for each action
    POINTS = {
        "incident_created": 10,
        "incident_resolved": 50,
        "incident_resolved_fast": 100,  # Under 1 hour
        "chat_message": 2,
        "community_post": 15,
        "community_comment": 5,
        "community_like_received": 3,
        "ticket_submitted": 10,
        "ticket_answered": 30,
        "knowledge_base_article": 25,
        "api_key_created": 5,
        "workspace_created": 20,
        "daily_login": 5,
    }
    
    # Badge definitions
    BADGES = {
        "first_blood": {
            "name": "First Blood",
            "icon": "🔥",
            "description": "Resolve your first incident",
            "requirement": lambda stats: stats.get("incidents_resolved", 0) >= 1
        },
        "speed_demon": {
            "name": "Speed Demon",
            "icon": "🚀",
            "description": "Resolve an incident in under 1 hour",
            "requirement": lambda stats: stats.get("fastest_resolution_hours", 999) < 1
        },
        "centurion": {
            "name": "Centurion",
            "icon": "💪",
            "description": "Log 100+ incidents",
            "requirement": lambda stats: stats.get("incidents_created", 0) >= 100
        },
        "root_cause_pro": {
            "name": "Root Cause Pro",
            "icon": "🧠",
            "description": "Resolve 25+ incidents",
            "requirement": lambda stats: stats.get("incidents_resolved", 0) >= 25
        },
        "team_player": {
            "name": "Team Player",
            "icon": "🤝",
            "description": "Help others by answering 10+ tickets",
            "requirement": lambda stats: stats.get("tickets_answered", 0) >= 10
        },
        "community_builder": {
            "name": "Community Builder",
            "icon": "🌐",
            "description": "Create 20+ community posts",
            "requirement": lambda stats: stats.get("community_posts", 0) >= 20
        },
        "knowledge_master": {
            "name": "Knowledge Master",
            "icon": "📚",
            "description": "Generate 10+ KB articles",
            "requirement": lambda stats: stats.get("kb_articles", 0) >= 10
        },
        "chatty": {
            "name": "Chatty",
            "icon": "💬",
            "description": "Send 100+ chat messages",
            "requirement": lambda stats: stats.get("chat_messages", 0) >= 100
        },
        "admin_power": {
            "name": "Admin Power",
            "icon": "👑",
            "description": "Have admin privileges",
            "requirement": lambda stats: stats.get("is_admin", False)
        },
        "night_owl": {
            "name": "Night Owl",
            "icon": "🦉",
            "description": "Be active between 12AM-5AM",
            "requirement": lambda stats: stats.get("night_activity", False)
        }
    }
    
    def calculate_level(self, points: int) -> dict:
        """Calculate level from points (100 points per level)."""
        level = (points // 100) + 1
        points_for_next = 100 - (points % 100)
        progress = points % 100
        
        return {
            "level": level,
            "current_points": points,
            "points_to_next_level": points_for_next,
            "progress_percent": progress
        }
    
    def check_badges(self, stats: dict) -> list:
        """Check which badges the user has earned."""
        earned = []
        for badge_id, badge in self.BADGES.items():
            try:
                if badge["requirement"](stats):
                    earned.append({
                        "id": badge_id,
                        "name": badge["name"],
                        "icon": badge["icon"],
                        "description": badge["description"]
                    })
            except:
                pass
        return earned
    
    def get_leaderboard(self, user_scores: list) -> list:
        """Sort users by points for leaderboard."""
        return sorted(user_scores, key=lambda x: x.get("points", 0), reverse=True)[:10]