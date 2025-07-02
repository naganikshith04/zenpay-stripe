# dependencies.py
from fastapi import Depends, HTTPException, Header
from sqlalchemy.orm import Session

from db.session import get_db
from db.models import User

def get_current_user(
    api_key: str = Header(..., convert_underscores=False, alias="api-key"), 
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.api_key == api_key).first()
    if not user:
        raise HTTPException(status_code=401, detail="Invalid API key")
    return user