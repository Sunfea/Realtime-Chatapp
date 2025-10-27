from sqlalchemy.orm import Session
import models
import schemas
import auth

def get_user_by_username(db: Session, username: str):
    return db.query(models.User).filter(models.User.username == username).first()

def get_user_by_email(db: Session, email: str):
    return db.query(models.User).filter(models.User.email == email).first()

def create_user(db: Session, user: schemas.UserCreate):
    # Check for both username AND email uniqueness
    if get_user_by_username(db, user.username):
        raise ValueError("Username already registered")
    if get_user_by_email(db, user.email):
        raise ValueError("Email already registered")
    
    hashed_password = auth.get_password_hash(user.password)
    db_user = models.User(
        full_name=user.full_name,
        username=user.username,
        email=user.email,
        hashed_password=hashed_password
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user