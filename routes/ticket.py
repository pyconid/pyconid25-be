import traceback

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import ValidationError
from sqlalchemy.orm import Session

from core.log import logger
from core.responses import (
    InternalServerError,
    NotFound,
    Ok,
    PaymentRequired,
    Unauthorized,
    common_response,
)
from core.security import get_user_from_token, oauth2_scheme
from models import get_db_sync
from models.Payment import PaymentStatus
from repository import payment as paymentRepo
from repository.checkin import (
    get_user_and_payment_by_payment_id,
    get_user_data_by_payment_id,
    set_user_checkin_status,
)
from repository.ticket import get_active_tickets
from schemas.checkin import (
    CheckinUserRequest,
    CheckinUserResponse,
    user_model_to_checkin_response,
)
from schemas.common import (
    InternalServerErrorResponse,
    NotFoundResponse,
    PaymentRequiredResponse,
    UnauthorizedResponse,
)
from schemas.ticket import (
    MyTicket,
    MyTicketInfo,
    MyTicketPayment,
    MyTicketResponse,
    MyTicketVoucher,
    TicketListResponse,
    TicketResponse,
)

router = APIRouter(prefix="/ticket", tags=["Ticket"])


@router.get("/", response_model=TicketListResponse)
def list_ticket(db: Session = Depends(get_db_sync)):
    try:
        tickets = get_active_tickets(db)
        results = [
            TicketResponse(
                id=str(t.id),
                name=t.name,
                price=t.price,
                user_participant_type=t.user_participant_type,
                is_sold_out=t.is_sold_out,
                description=t.description,
            )
            for t in tickets
        ]
        return TicketListResponse(results=results)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {e}")


@router.get(
    "/me",
    responses={
        "200": {"model": MyTicketResponse},
        "401": {"model": UnauthorizedResponse},
        "500": {"model": InternalServerErrorResponse},
    },
)
async def get_my_ticket(
    db: Session = Depends(get_db_sync),
    token: str = Depends(oauth2_scheme),
):
    try:
        user = get_user_from_token(db=db, token=token)
        if user is None:
            return common_response(Unauthorized(message="Unauthorized"))

        payment = paymentRepo.get_user_paid_payment(db=db, user_id=str(user.id))

        if not payment:
            return common_response(
                Ok(data={"data": None, "message": "No ticket purchased yet"})
            )

        ticket = payment.ticket
        voucher = payment.voucher

        response_data = MyTicket(
            ticket=MyTicketInfo(
                id=str(ticket.id),
                name=ticket.name,
                price=ticket.price,
                participant_type=ticket.user_participant_type,
            ),
            payment=MyTicketPayment(
                id=str(payment.id),
                amount=payment.amount,
                paid_at=payment.paid_at,
                voucher=(
                    MyTicketVoucher(
                        code=voucher.code,
                        value=voucher.value,
                        participant_type=voucher.type,
                    )
                    if voucher
                    else None
                ),
            ),
            participant_type=user.participant_type or ticket.user_participant_type,
        )

        return common_response(
            Ok(
                data={
                    "data": response_data.model_dump(mode="json"),
                    "message": "Ticket retrieved successfully",
                }
            )
        )
    except Exception as e:
        traceback.print_exc()
        logger.error(f"Error in get_my_ticket: {e}")
        return common_response(
            InternalServerError(error=f"Internal Server Error: {str(e)}")
        )


@router.get(
    "/checkin/{payment_id}",
    responses={
        "200": {"model": CheckinUserResponse},
        "404": {"model": NotFoundResponse},
        "500": {"model": InternalServerErrorResponse},
    },
)
async def checkin(payment_id: str, db: Session = Depends(get_db_sync)):
    """Endpoint to get user check-in data based on Payment ID

    Args:
        payment_id (str): Payment ID
        db (Session, optional): DB session. Defaults to Depends(get_db_sync).

    Returns:
        CheckinUserResponse: User check-in data
    """
    try:
        result = get_user_data_by_payment_id(db, payment_id)
        if result is None:
            return common_response(
                NotFound(message=f"No user found for payment ID: {payment_id}")
            )
        response = user_model_to_checkin_response(result)
    except ValidationError as ve:
        traceback.print_exc()
        logger.error(f"Validation error in checkin: {ve}")
        return common_response(
            InternalServerError(error=f"Validation Error: {str(ve)}")
        )
    except Exception as e:
        traceback.print_exc()
        logger.error(f"Error in checkin: {e}")
        return common_response(
            InternalServerError(error=f"Internal Server Error: {str(e)}")
        )
    return common_response(
        Ok(
            data={
                "data": response.model_dump(mode="json"),
                "message": "Successfully retrieved user checkin data",
            }
        )
    )


@router.patch(
    "/checkin",
    responses={
        "200": {"model": CheckinUserResponse},
        "401": {"model": UnauthorizedResponse},
        "402": {"model": PaymentRequiredResponse},
        "404": {"model": NotFoundResponse},
        "500": {"model": InternalServerErrorResponse},
    },
)
async def checkin_user(
    request: Request,
    payload: CheckinUserRequest,
    db: Session = Depends(get_db_sync),
    token: str = Depends(oauth2_scheme),
):
    logger.info(f"Checkin request received: {payload}")
    try:
        checkin_staff_user = get_user_from_token(db=db, token=token)
        if checkin_staff_user is None:
            logger.error("Unauthorized check-in attempt")
            return common_response(Unauthorized(message="Unauthorized"))
        
        user_and_payment = get_user_and_payment_by_payment_id(db, payload.payment_id)
        if user_and_payment is None:
            return common_response(
                NotFound(message=f"No user found for payment ID: {payload.payment_id}")
            )
        user, payment = user_and_payment
        if payment.status != PaymentStatus.PAID:
            return common_response(
                PaymentRequired(
                    detail=f"Payment with ID {payload.payment_id} is not paid yet."
                )
            )
        checkin_status = True
        updated_user = set_user_checkin_status(
            db=db, user_id=str(user.id), day=payload.day, status=checkin_status, updated_by=str(checkin_staff_user.id)
        )

        if updated_user is None:
            return common_response(
                InternalServerError(
                    error="Failed to process check-in. Please try again or contact support."
                )
            )
    except Exception as e:
        traceback.print_exc()
        logger.error(f"Error in checkin_user: {e}")
        return common_response(
            InternalServerError(error=f"Internal Server Error: {str(e)}")
        )
    response = user_model_to_checkin_response(updated_user)
    return common_response(
        Ok(
            data={
                "data": response.model_dump(mode="json"),
                "message": "User check-in successful",
            }
        )
    )


@router.patch(
    "/checkin/reset",
    responses={
        "200": {"model": CheckinUserResponse},
        "401": {"model": UnauthorizedResponse},
        "402": {"model": PaymentRequiredResponse},
        "404": {"model": NotFoundResponse},
        "500": {"model": InternalServerErrorResponse},
    },
)
async def checkin_user_reset(
    request: Request,
    payload: CheckinUserRequest,
    db: Session = Depends(get_db_sync),
    token: str = Depends(oauth2_scheme),
):
    logger.info(f"Checkin Reset request received: {payload}")
    try:
        checkin_staff_user = get_user_from_token(db=db, token=token)
        if checkin_staff_user is None:
            logger.error("Unauthorized check-in reset attempt")
            return common_response(Unauthorized(message="Unauthorized"))
        
        user= get_user_data_by_payment_id(db, payload.payment_id)
        if user is None:
            return common_response(
                NotFound(message=f"No user found for payment ID: {payload.payment_id}")
            )
        checkin_status = False
        updated_user = set_user_checkin_status(
            db=db, user_id=str(user.id), day=payload.day, status=checkin_status, updated_by=str(checkin_staff_user.id)
        )

        if updated_user is None:
            return common_response(
                InternalServerError(
                    error="Failed to process check-in reset. Please try again or contact support."
                )
            )
    except Exception as e:
        traceback.print_exc()
        logger.error(f"Error in checkin_user_reset: {e}")
        return common_response(
            InternalServerError(error=f"Internal Server Error: {str(e)}")
        )
    response = user_model_to_checkin_response(updated_user)
    return common_response(
        Ok(
            data={
                "data": response.model_dump(mode="json"),
                "message": "Reset user check-in successful",
            }
        )
    )