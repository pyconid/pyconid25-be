from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from models import get_db_sync
from repository.voucher import (
    insert_voucher,
    update_status,
    update_whitelist,
    update_quota,
    update_value,
    update_type_voucher,
    get_vouchers_per_page,
)
from schemas.voucher import (
    VoucherCreateRequest,
    VoucherUpdateStatusRequest,
    VoucherUpdateWhitelistRequest,
    VoucherUpdateQuotaRequest,
    VoucherUpdateValueRequest,
    VoucherUpdateTypeRequest,
    VoucherResponse,
    VoucherQuery,
    VoucherListResponse,
)

router = APIRouter(prefix="/voucher", tags=["Voucher"])


@router.get("/", response_model=VoucherListResponse)
def list_vouchers(query: VoucherQuery = Depends(), db: Session = Depends(get_db_sync)):
    try:
        data = get_vouchers_per_page(
            db=db,
            page=query.page,
            page_size=query.page_size,
            search=query.search,
        )
        return VoucherListResponse.model_validate(data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {e}")


@router.post("/", response_model=VoucherResponse)
def create_voucher(request: VoucherCreateRequest, db: Session = Depends(get_db_sync)):
    try:
        voucher = insert_voucher(
            db=db,
            code=request.code,
            value=request.value,
            quota=request.quota,
            type=request.type,
            email_whitelist=request.email_whitelist,
            is_active=request.is_active,
        )
        return VoucherResponse(
            id=str(voucher.id),
            code=voucher.code,
            value=voucher.value,
            type=voucher.type,
            email_whitelist=voucher.email_whitelist,
            quota=voucher.quota,
            is_active=voucher.is_active,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {e}")


@router.patch("/{voucher_id}/status", response_model=VoucherResponse)
def update_voucher_status(
    voucher_id: str,
    request: VoucherUpdateStatusRequest,
    db: Session = Depends(get_db_sync),
):
    try:
        voucher = update_status(db, voucher_id, request.is_active)
        if not voucher:
            raise HTTPException(status_code=404, detail="Voucher not found")
        return VoucherResponse(
            id=str(voucher.id),
            code=voucher.code,
            value=voucher.value,
            type=voucher.type,
            email_whitelist=voucher.email_whitelist,
            quota=voucher.quota,
            is_active=voucher.is_active,
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {e}")


@router.patch("/{voucher_id}/whitelist", response_model=VoucherResponse)
def update_voucher_whitelist(
    voucher_id: str,
    request: VoucherUpdateWhitelistRequest,
    db: Session = Depends(get_db_sync),
):
    try:
        voucher = update_whitelist(db, voucher_id, request.email_whitelist)
        if not voucher:
            raise HTTPException(status_code=404, detail="Voucher not found")
        return VoucherResponse(
            id=str(voucher.id),
            code=voucher.code,
            value=voucher.value,
            type=voucher.type,
            email_whitelist=voucher.email_whitelist,
            quota=voucher.quota,
            is_active=voucher.is_active,
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {e}")


@router.patch("/{voucher_id}/quota", response_model=VoucherResponse)
def update_voucher_quota(
    voucher_id: str,
    request: VoucherUpdateQuotaRequest,
    db: Session = Depends(get_db_sync),
):
    try:
        voucher = update_quota(db, voucher_id, request.quota)
        if not voucher:
            raise HTTPException(status_code=404, detail="Voucher not found")
        return VoucherResponse(
            id=str(voucher.id),
            code=voucher.code,
            value=voucher.value,
            type=voucher.type,
            email_whitelist=voucher.email_whitelist,
            quota=voucher.quota,
            is_active=voucher.is_active,
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {e}")


@router.patch("/{voucher_id}/value", response_model=VoucherResponse)
def update_voucher_value(
    voucher_id: str,
    request: VoucherUpdateValueRequest,
    db: Session = Depends(get_db_sync),
):
    try:
        voucher = update_value(db, voucher_id, request.value)
        if not voucher:
            raise HTTPException(status_code=404, detail="Voucher not found")
        return VoucherResponse(
            id=str(voucher.id),
            code=voucher.code,
            value=voucher.value,
            type=voucher.type,
            email_whitelist=voucher.email_whitelist,
            quota=voucher.quota,
            is_active=voucher.is_active,
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {e}")


@router.patch("/{voucher_id}/type", response_model=VoucherResponse)
def update_voucher_type(
    voucher_id: str,
    request: VoucherUpdateTypeRequest,
    db: Session = Depends(get_db_sync),
):
    try:
        voucher = update_type_voucher(db, voucher_id, request.type)
        if not voucher:
            raise HTTPException(status_code=404, detail="Voucher not found")
        return VoucherResponse(
            id=str(voucher.id),
            code=voucher.code,
            value=voucher.value,
            type=voucher.type,
            email_whitelist=voucher.email_whitelist,
            quota=voucher.quota,
            is_active=voucher.is_active,
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {e}")
