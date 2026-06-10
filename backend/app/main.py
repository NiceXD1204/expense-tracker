from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, HTTPException
from prometheus_fastapi_instrumentator import Instrumentator
from sqlalchemy import func
from sqlalchemy.orm import Session

from . import models, schemas
from .database import engine, get_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Create tables on startup (fine for this project; a real product would use migrations)
    models.Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(title="Expense Tracker API", version="1.0.0", lifespan=lifespan)

# Exposes /metrics for Prometheus (scraped via the backend chart's ServiceMonitor).
Instrumentator().instrument(app).expose(app)


@app.get("/healthz")
def health():
    """Used by Kubernetes liveness/readiness probes."""
    return {"status": "ok"}


@app.get("/expenses", response_model=list[schemas.ExpenseOut])
def list_expenses(db: Session = Depends(get_db)):
    return db.query(models.Expense).order_by(models.Expense.created_at.desc()).all()


@app.post("/expenses", response_model=schemas.ExpenseOut, status_code=201)
def create_expense(expense: schemas.ExpenseCreate, db: Session = Depends(get_db)):
    db_expense = models.Expense(**expense.model_dump())
    db.add(db_expense)
    db.commit()
    db.refresh(db_expense)
    return db_expense


@app.delete("/expenses/{expense_id}", status_code=204)
def delete_expense(expense_id: int, db: Session = Depends(get_db)):
    expense = db.get(models.Expense, expense_id)
    if expense is None:
        raise HTTPException(status_code=404, detail="Expense not found")
    db.delete(expense)
    db.commit()


@app.get("/summary", response_model=list[schemas.CategorySummary])
def summary(db: Session = Depends(get_db)):
    rows = (
        db.query(models.Expense.category, func.sum(models.Expense.amount).label("total"))
        .group_by(models.Expense.category)
        .all()
    )
    return [{"category": c, "total": round(t, 2)} for c, t in rows]
