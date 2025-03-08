from database import get_db
from bson import ObjectId

def create_gamification_collection():
    """Create and populate the gamification collection with initial badge data"""
    db = get_db()
    
    # Check if collection already exists
    if "gamification" in db.list_collection_names():
        print("Gamification collection already exists.")
        return
    
    # Create the collection
    db.create_collection("gamification")
    print("Created gamification collection.")
    
    # Sample badge data
    badges = [
        {
            "_id": ObjectId(),
            "resource_type": "badge",
            "name": "Learning Pioneer",
            "description": "Completed your first learning module and started your journey.",
            "short_description": "First module completed",
            "category": "learning",
            "color": "#4CAF50",
            "icon": "school",
            "xp_awarded": 50,
            "conditions": {
                "type": "module_completion",
                "threshold": 1
            }
        },
        {
            "_id": ObjectId(),
            "resource_type": "badge",
            "name": "Quiz Master",
            "description": "Achieved a perfect score on 5 different quizzes.",
            "short_description": "5 perfect quiz scores",
            "category": "assessment",
            "color": "#2196F3",
            "icon": "quiz",
            "xp_awarded": 100,
            "conditions": {
                "type": "perfect_quiz",
                "threshold": 5
            }
        },
        {
            "_id": ObjectId(),
            "resource_type": "badge",
            "name": "Consistent Learner",
            "description": "Maintained a 7-day learning streak.",
            "short_description": "7-day streak",
            "category": "engagement",
            "color": "#FF9800",
            "icon": "calendar_month",
            "xp_awarded": 75,
            "conditions": {
                "type": "login_streak",
                "threshold": 7
            },
            "reward": "25% XP boost for the next 3 days"
        },
        {
            "_id": ObjectId(),
            "resource_type": "badge",
            "name": "Skill Improver",
            "description": "Improved at least one skill to level 3.",
            "short_description": "Skill at level 3",
            "category": "skill",
            "color": "#9C27B0",
            "icon": "trending_up",
            "xp_awarded": 150,
            "conditions": {
                "type": "skill_level",
                "threshold": 3
            }
        },
        {
            "_id": ObjectId(),
            "resource_type": "badge",
            "name": "Community Helper",
            "description": "Made 5 helpful contributions to the community.",
            "short_description": "5 community contributions",
            "category": "community",
            "color": "#E91E63",
            "icon": "people",
            "xp_awarded": 125,
            "conditions": {
                "type": "community_contribution",
                "threshold": 5
            }
        }
    ]
    
    # Insert the badge data
    db.gamification.insert_many(badges)
    print(f"Added {len(badges)} badges to the gamification collection.")

if __name__ == "__main__":
    create_gamification_collection()