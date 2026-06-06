from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Post
from app.schemas.post_schema import PostOut
router=APIRouter(prefix="/posts", tags=["posts"])
@router.get("", response_model=list[PostOut])
def list_posts(limit:int=50, offset:int=0, db: Session=Depends(get_db)):
    return db.query(Post).order_by(Post.id.desc()).offset(offset).limit(min(limit, 200)).all()
@router.get("/top", response_model=list[PostOut])
def top_posts(limit:int=10, db: Session=Depends(get_db)):
    return db.query(Post).order_by(Post.final_score.desc()).limit(min(limit, 50)).all()
@router.get("/{post_id}", response_model=PostOut)
def get_post(post_id:int, db: Session=Depends(get_db)):
    obj=db.get(Post,post_id)
    if not obj: raise HTTPException(404,"post not found")
    return obj
