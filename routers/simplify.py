from fastapi import APIRouter, Depends, HTTPException
from typing import List, Optional
from models.user import User, TextHistory, TextHistoryCreate
from routers.auth import oauth2_scheme
from database.database import get_db
from database.models import TextHistory as DBTextHistory, User as DBUser
from sqlalchemy.orm import Session
from jose import jwt
from utils.auth_utils import SECRET_KEY, ALGORITHM
from utils.simplify_agent import SimplifyAgent
from pydantic import BaseModel

router = APIRouter()
simplify_agent = SimplifyAgent()

class SimplifyRequest(BaseModel):
    text: str
    previous_point_id: Optional[int] = None

@router.post("/text", response_model=TextHistory)
async def simplify_text(
    request: SimplifyRequest,
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
):
    try:
        # Get user from token
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        user = db.query(DBUser).filter(DBUser.email == email).first()
        
        if request.previous_point_id:
            # Handle follow-up request
            result = await simplify_agent.handle_follow_up(
                text=request.text,
                user_id=user.id,
                previous_point_id=request.previous_point_id
            )
        else:
            # Handle new simplification request
            result = await simplify_agent.simplify_text(
                text=request.text,
                user_id=user.id
            )
        
        # Save to MySQL database for history
        db_history = DBTextHistory(
            user_id=user.id,
            original_text=result["original_text"],
            simplified_text=result["simplified_text"],
            vector_id=result["point_id"]
        )
        db.add(db_history)
        db.commit()
        db.refresh(db_history)
        
        return db_history
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/history", response_model=List[TextHistory])
async def get_simplification_history(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
):
    try:
        # Get user from token
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        user = db.query(DBUser).filter(DBUser.email == email).first()
        
        # Get user's history from MySQL
        history = db.query(DBTextHistory).filter(
            DBTextHistory.user_id == user.id
        ).order_by(DBTextHistory.created_at.desc()).all()
        
        return history
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) 