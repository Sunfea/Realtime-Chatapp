from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List
from database import get_db
import models
import schemas
import auth

router = APIRouter()

@router.get("/me", response_model=schemas.UserPublic)
async def read_users_me(current_user: models.User = Depends(auth.get_current_user)):
    return current_user

@router.put("/me", response_model=schemas.UserPublic)
async def update_user_profile(
    full_name: str,
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    current_user.full_name = full_name
    db.commit()
    db.refresh(current_user)
    return current_user

@router.get("/search", response_model=List[schemas.UserPublic])
async def search_users(
    q: str = Query(..., min_length=1, max_length=20),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    # Normalize search term to lowercase
    search_term = q.lower().strip()
    
    # Use ilike for case-insensitive search and broader matching
    users = db.query(models.User).filter(
        models.User.username.ilike(f"{search_term}%"),  # Changed to ilike
        models.User.id != current_user.id
    ).limit(10).all()
    
    return users

# @router.get("/debug/all-users", response_model=List[schemas.UserPublic])
# async def get_all_users(db: Session = Depends(get_db)):
#     """Temporary endpoint to see all users - remove in production!"""
#     users = db.query(models.User).all()
#     return users