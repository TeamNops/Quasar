from fastapi import APIRouter, Depends, HTTPException, Header
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
from bson import ObjectId
import jwt
from datetime import datetime

from database import get_db
from jwt_config import settings

router = APIRouter(
    prefix="/api/gamification",
    tags=["gamification"],
    responses={404: {"description": "Not found"}},
)

# Define models for gamification features
class Badge(BaseModel):
    id: str
    name: str
    description: str
    short_description: str
    category: str
    color: str
    icon: str
    xp_awarded: int
    conditions: Dict[str, Any]
    reward: Optional[str] = None
    
class UserXP(BaseModel):
    current: int
    level: int
    level_threshold: int
    total_earned: int

class UserAchievement(BaseModel):
    badge_id: str
    earned_date: datetime
    
class UserBadgeProgress(BaseModel):
    badge_id: str
    progress: Dict[str, Any]

# XP points for different activities
XP_REWARDS = {
    "complete_assessment": 100,
    "improve_skill_level": 150,
    "complete_module": 50,
    "perfect_quiz_score": 75,
    "daily_login": 10,
    "learning_streak_day": 15,  # Per day in streak
    "contribute_to_community": 25,
}

# Get user's XP and level
@router.get("/xp")
async def get_user_xp(authorization: str = Header(None)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid authentication token")
    
    token = authorization.replace("Bearer ", "")
    
    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
        user_id = payload.get("sub")
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Invalid authentication token")
    
    db = get_db()
    user_data = db.users.find_one({"_id": ObjectId(user_id)})
    
    if not user_data:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Get XP data or initialize if not present
    xp_data = user_data.get("xp_data", {
        "current": 0,
        "level": 1,
        "level_threshold": 100,
        "total_earned": 0
    })
    
    return {
        "xp": xp_data["current"],
        "level": xp_data["level"],
        "level_threshold": xp_data["level_threshold"],
        "total_earned": xp_data["total_earned"]
    }

# Award XP points for an activity
@router.post("/award-xp")
async def award_xp(
    activity_data: Dict[str, Any],
    authorization: str = Header(None)
):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid authentication token")
    
    token = authorization.replace("Bearer ", "")
    
    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
        user_id = payload.get("sub")
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Invalid authentication token")
    
    db = get_db()
    
    # Get activity type and any bonus multipliers
    activity_type = activity_data.get("activity_type")
    bonus_multiplier = activity_data.get("bonus_multiplier", 1.0)
    
    if activity_type not in XP_REWARDS:
        raise HTTPException(status_code=400, detail="Invalid activity type")
    
    # Calculate XP to award
    xp_to_award = int(XP_REWARDS[activity_type] * bonus_multiplier)
    
    # Update user's XP data
    user = db.users.find_one({"_id": ObjectId(user_id)})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Get current XP data or initialize
    xp_data = user.get("xp_data", {
        "current": 0,
        "level": 1,
        "level_threshold": 100,
        "total_earned": 0
    })
    
    # Update XP
    xp_data["current"] += xp_to_award
    xp_data["total_earned"] += xp_to_award
    
    # Check for level up
    level_up = False
    while xp_data["current"] >= xp_data["level_threshold"]:
        xp_data["current"] -= xp_data["level_threshold"]
        xp_data["level"] += 1
        # Each level requires more XP
        xp_data["level_threshold"] = calculate_next_level_threshold(xp_data["level"])
        level_up = True
    
    # Update user document
    db.users.update_one(
        {"_id": ObjectId(user_id)},
        {"$set": {"xp_data": xp_data}}
    )
    
    # Log XP activity
    db.xp_activities.insert_one({
        "user_id": ObjectId(user_id),
        "activity_type": activity_type,
        "xp_awarded": xp_to_award,
        "timestamp": datetime.utcnow(),
        "metadata": activity_data.get("metadata", {})
    })
    
    return {
        "xp_awarded": xp_to_award,
        "new_xp": xp_data["current"],
        "level": xp_data["level"],
        "level_threshold": xp_data["level_threshold"],
        "level_up": level_up
    }

# Get user's badges
@router.get("/badges")
async def get_user_badges(authorization: str = Header(None)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid authentication token")
    
    token = authorization.replace("Bearer ", "")
    
    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
        user_id = payload.get("sub")
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Invalid authentication token")
    
    db = get_db()
    
    # Get all available badges
    all_badges = list(db.badges.find({}))
    
    # Get user's earned badges
    user_data = db.users.find_one({"_id": ObjectId(user_id)})
    if not user_data:
        raise HTTPException(status_code=404, detail="User not found")
    
    earned_badges = user_data.get("earned_badges", [])
    badge_progress = user_data.get("badge_progress", {})
    
    # Prepare response with unlocked and progress information
    result = []
    for badge in all_badges:
        badge_id = str(badge["_id"])
        is_unlocked = any(eb["badge_id"] == badge_id for eb in earned_badges)
        
        badge_data = {
            "id": badge_id,
            "name": badge["name"],
            "description": badge["description"],
            "short_description": badge["short_description"],
            "category": badge["category"],
            "color": badge["color"],
            "icon": badge["icon"],
            "unlocked": is_unlocked,
            "xp_awarded": badge["xp_awarded"],
        }
        
        if is_unlocked:
            # Find when it was earned
            for eb in earned_badges:
                if eb["badge_id"] == badge_id:
                    badge_data["earned_date"] = eb["earned_date"]
                    break
                    
            if "reward" in badge:
                badge_data["reward"] = badge["reward"]
        else:
            # Add progress info
            if badge_id in badge_progress:
                progress_data = badge_progress[badge_id]
                badge_data["progress"] = {
                    "current": progress_data["current"],
                    "required": badge["conditions"]["threshold"]
                }
        
        result.append(badge_data)
    
    return {"badges": result}

# Helper function to calculate next level threshold
def calculate_next_level_threshold(level):
    # Formula: 100 * level^1.5
    return int(100 * (level ** 1.5))