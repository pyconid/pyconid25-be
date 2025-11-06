from typing import Optional
from sqlalchemy import select, func
from sqlalchemy.orm import Session
from models.Voucher import Voucher
from schemas.voucher import VoucherResponseItem


def insert_voucher(
    db: Session,
    code: str,
    value: int,
    quota: int,
    type: str | None = None,
    email_whitelist: dict | None = None,
    is_active: bool = False,
) -> Voucher:
    voucher = Voucher(
        code=code,
        value=value,
        quota=quota,
        type=type,
        email_whitelist=email_whitelist,
        is_active=is_active,
    )
    db.add(voucher)
    db.commit()
    db.refresh(voucher)
    return voucher


def update_status(db: Session, voucher_id: str, is_active: bool) -> Optional[Voucher]:
    query = select(Voucher).where(Voucher.id == voucher_id)
    voucher = db.execute(query).scalars().first()
    if voucher:
        voucher.is_active = is_active
        db.commit()
        db.refresh(voucher)
    return voucher


def update_whitelist(
    db: Session, voucher_id: str, email_whitelist: dict
) -> Optional[Voucher]:
    query = select(Voucher).where(Voucher.id == voucher_id)
    voucher = db.execute(query).scalars().first()
    if voucher:
        voucher.email_whitelist = email_whitelist
        db.commit()
        db.refresh(voucher)
    return voucher


def update_quota(db: Session, voucher_id: str, quota: int) -> Optional[Voucher]:
    query = select(Voucher).where(Voucher.id == voucher_id)
    voucher = db.execute(query).scalars().first()
    if voucher:
        voucher.quota = quota
        db.commit()
        db.refresh(voucher)
    return voucher


def update_value(db: Session, voucher_id: str, value: int) -> Optional[Voucher]:
    query = select(Voucher).where(Voucher.id == voucher_id)
    voucher = db.execute(query).scalars().first()
    if voucher:
        voucher.value = value
        db.commit()
        db.refresh(voucher)
    return voucher


def update_type_voucher(db: Session, voucher_id: str, type: str) -> Optional[Voucher]:
    query = select(Voucher).where(Voucher.id == voucher_id)
    voucher = db.execute(query).scalars().first()
    if voucher:
        voucher.type = type
        db.commit()
        db.refresh(voucher)
    return voucher


def get_vouchers_per_page(
    db: Session,
    page: int,
    page_size: int,
    search: Optional[str] = None,
) -> dict:
    offset = (page - 1) * page_size

    stmt = select(Voucher)

    if search:
        stmt = stmt.where(
            Voucher.code.ilike(f"%{search}%"),
        )

    total_count = db.scalar(select(func.count()).select_from(stmt.subquery()))

    stmt = stmt.offset(offset).limit(page_size)

    results = db.scalars(stmt).all()
    results_schema = [VoucherResponseItem.model_validate(r) for r in results]
    page_count = (total_count + page_size - 1) // page_size if total_count else 0

    return {
        "page": page,
        "page_size": page_size,
        "count": total_count,
        "page_count": page_count,
        "results": results_schema,
    }
