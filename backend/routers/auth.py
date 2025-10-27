from fastapi import APIRouter, Depends, HTTPException, status, Form
from sqlalchemy.orm import Session
from database import get_db
import schemas, crud, auth

router = APIRouter()

@router.post("/register", response_model=schemas.UserPublic)
def register(user: schemas.UserCreate, db: Session = Depends(get_db)):
    db_user = crud.get_user_by_username(db, username=user.username)
    if db_user:
        raise HTTPException(status_code=400, detail="Username already registered")
    return crud.create_user(db=db, user=user)

@router.post("/login")
def login(form_data: schemas.UserLogin, db: Session = Depends(get_db)):
    user = crud.get_user_by_username(db, username=form_data.username)
    if not user or not auth.verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=400, detail="Incorrect username or password")
    return {"access_token": auth.create_access_token(data={"sub": user.username}), "token_type": "bearer"}