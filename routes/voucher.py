from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from core.responses import Forbidden, Unauthorized, common_response
from core.security import get_current_user
from models import get_db_sync
from models.User import MANAGEMENT_PARTICIPANT, User
from repository.voucher import (
    get_voucher_by_id,
    insert_voucher,
    update_status,
    update_voucher,
    update_whitelist,
    update_quota,
    update_value,
    update_type_voucher,
    get_vouchers_per_page,
)
from schemas.voucher import (
    VoucherCreateRequest,
    VoucherUpdateRequest,
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
def list_vouchers(
    query: VoucherQuery = Depends(),
    db: Session = Depends(get_db_sync),
    user: User = Depends(get_current_user),
):
    try:
        if user is None:
            return common_response(Unauthorized(message="Unauthorized"))

        if user.participant_type != MANAGEMENT_PARTICIPANT:
            return common_response(Forbidden())

        data = get_vouchers_per_page(
            db=db,
            page=query.page,
            page_size=query.page_size,
            search=query.search,
        )
        return VoucherListResponse.model_validate(data)
    except Exception as e:
        import traceback

        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {e}")


@router.post("/", response_model=VoucherResponse)
def create_voucher(
    request: VoucherCreateRequest,
    db: Session = Depends(get_db_sync),
    user: User = Depends(get_current_user),
):
    try:
        if user is None:
            return common_response(Unauthorized(message="Unauthorized"))

        if user.participant_type != MANAGEMENT_PARTICIPANT:
            return common_response(Forbidden())

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
        import traceback

        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {e}")


@router.get("/{voucher_id}", response_model=VoucherResponse)
def get_voucher(
    voucher_id: str,
    db: Session = Depends(get_db_sync),
    user: User = Depends(get_current_user),
):
    if user is None:
        return common_response(Unauthorized(message="Unauthorized"))

    if user.participant_type != MANAGEMENT_PARTICIPANT:
        return common_response(Forbidden())

    voucher = get_voucher_by_id(db=db, id=voucher_id)
    if voucher is None:
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


@router.put("/{voucher_id}", response_model=VoucherResponse)
def update_voucher_whole(
    voucher_id: str,
    request: VoucherUpdateRequest,
    db: Session = Depends(get_db_sync),
    user: User = Depends(get_current_user),
):
    if user is None:
        return common_response(Unauthorized(message="Unauthorized"))

    if user.participant_type != MANAGEMENT_PARTICIPANT:
        return common_response(Forbidden())

    voucher = get_voucher_by_id(db=db, id=voucher_id)
    if voucher is None:
        raise HTTPException(status_code=404, detail="Voucher not found")

    voucher = update_voucher(
        db=db,
        voucher=voucher,
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


@router.patch("/{voucher_id}/status", response_model=VoucherResponse)
def update_voucher_status(
    voucher_id: str,
    request: VoucherUpdateStatusRequest,
    db: Session = Depends(get_db_sync),
    user: User = Depends(get_current_user),
):
    try:
        if user is None:
            return common_response(Unauthorized(message="Unauthorized"))

        if user.participant_type != MANAGEMENT_PARTICIPANT:
            return common_response(Forbidden())

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
        import traceback

        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {e}")


@router.patch("/{voucher_id}/whitelist", response_model=VoucherResponse)
def update_voucher_whitelist(
    voucher_id: str,
    request: VoucherUpdateWhitelistRequest,
    db: Session = Depends(get_db_sync),
    user: User = Depends(get_current_user),
):
    try:
        if user is None:
            return common_response(Unauthorized(message="Unauthorized"))

        if user.participant_type != MANAGEMENT_PARTICIPANT:
            return common_response(Forbidden())

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
        import traceback

        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {e}")


@router.patch("/{voucher_id}/quota", response_model=VoucherResponse)
def update_voucher_quota(
    voucher_id: str,
    request: VoucherUpdateQuotaRequest,
    db: Session = Depends(get_db_sync),
    user: User = Depends(get_current_user),
):
    try:
        if user is None:
            return common_response(Unauthorized(message="Unauthorized"))

        if user.participant_type != MANAGEMENT_PARTICIPANT:
            return common_response(Forbidden())

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
        import traceback

        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {e}")


@router.patch("/{voucher_id}/value", response_model=VoucherResponse)
def update_voucher_value(
    voucher_id: str,
    request: VoucherUpdateValueRequest,
    db: Session = Depends(get_db_sync),
    user: User = Depends(get_current_user),
):
    try:
        if user is None:
            return common_response(Unauthorized(message="Unauthorized"))

        if user.participant_type != MANAGEMENT_PARTICIPANT:
            return common_response(Forbidden())

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
        import traceback

        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {e}")


@router.patch("/{voucher_id}/type", response_model=VoucherResponse)
def update_voucher_type(
    voucher_id: str,
    request: VoucherUpdateTypeRequest,
    db: Session = Depends(get_db_sync),
    user: User = Depends(get_current_user),
):
    try:
        if user is None:
            return common_response(Unauthorized(message="Unauthorized"))

        if user.participant_type != MANAGEMENT_PARTICIPANT:
            return common_response(Forbidden())

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
        import traceback

        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {e}")
