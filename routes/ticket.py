import traceback

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from core.log import logger
from core.responses import InternalServerError, Ok, Unauthorized, common_response, NotFound
from core.security import get_user_from_token, oauth2_scheme
from models import get_db_sync
from repository import payment as paymentRepo
from repository.checkin import get_user_data_by_payment_id
from repository.ticket import get_active_tickets
from schemas.checkin import CheckinUserResponse
from schemas.common import (
    InternalServerErrorResponse,
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


@router.get("/checkin/{payment_id}")
async def checkin(payment_id: str, db: Session = Depends(get_db_sync)):
    try:
        result = get_user_data_by_payment_id(db, payment_id)
        if result is None:
            return common_response(
                NotFound(
                    message=f"No user found for payment ID: {payment_id}"
                )
            )
        response = CheckinUserResponse(
            id=str(result.id),
            email=result.email,
            first_name=result.first_name,
            last_name=result.last_name,
            t_shirt_size=result.t_shirt_size,
            participant_type=result.participant_type
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