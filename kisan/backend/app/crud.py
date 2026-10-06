from datetime import date
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import or_, select
from sqlalchemy.orm import Session
from .auth import current_user
from .db import get_db
from .models import User

def row(o): return {c.name: getattr(o, c.name) for c in o.__table__.columns}

def crud_router(path, Model, Schema):
    """List/create/update/delete. Every query is filtered by user_id."""
    r = APIRouter(prefix=f"/api/{path}", tags=[path])

    def own(db, u, id):
        o = db.scalar(select(Model).where(Model.id == id, Model.user_id == u.id))
        if not o: raise HTTPException(404, "Record not found")
        return o

    def check_crop(db, u, data):
        cid = getattr(data, "crop_id", None)
        if cid:
            from .models import Crop
            if not db.scalar(select(Crop).where(Crop.id == cid, Crop.user_id == u.id)):
                raise HTTPException(400, "Invalid crop")

    @r.get("")
    def list_(q: Optional[str] = None, date_from: Optional[date] = None, date_to: Optional[date] = None,
              crop_id: Optional[int] = None, category: Optional[str] = None, month: Optional[str] = None,
              db: Session = Depends(get_db), u: User = Depends(current_user)):
        s = select(Model).where(Model.user_id == u.id)
        dc = getattr(Model, "date", None)
        if dc is not None:
            if date_from: s = s.where(dc >= date_from)
            if date_to: s = s.where(dc <= date_to)
            if month: s = s.where(dc >= date.fromisoformat(month + "-01"))\
                           .where(dc < (date(int(month[:4]) + (month[5:] == "12"), int(month[5:]) % 12 + 1, 1)))
            s = s.order_by(dc.desc(), Model.id.desc())
        if crop_id and hasattr(Model, "crop_id"): s = s.where(Model.crop_id == crop_id)
        if category and hasattr(Model, "category"): s = s.where(Model.category == category)
        if q:
            cols = [getattr(Model, c).ilike(f"%{q}%") for c in ("description", "notes", "name", "scheme", "buyer") if hasattr(Model, c)]
            if cols: s = s.where(or_(*cols))
        return [row(o) for o in db.scalars(s)]

    @r.post("", status_code=201)
    def create(data: Schema, db: Session = Depends(get_db), u: User = Depends(current_user)):
        check_crop(db, u, data)
        o = Model(user_id=u.id, **data.model_dump())
        db.add(o); db.commit(); db.refresh(o)
        return row(o)

    @r.put("/{id}")
    def update(id: int, data: Schema, db: Session = Depends(get_db), u: User = Depends(current_user)):
        o = own(db, u, id); check_crop(db, u, data)
        for k, v in data.model_dump().items(): setattr(o, k, v)
        db.commit(); db.refresh(o)
        return row(o)

    @r.delete("/{id}")
    def delete(id: int, db: Session = Depends(get_db), u: User = Depends(current_user)):
        db.delete(own(db, u, id)); db.commit()
        return {"ok": True}

    return r
