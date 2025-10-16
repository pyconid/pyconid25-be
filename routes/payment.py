import traceback
from fastapi import APIRouter, Depends, Header
from sqlalchemy.orm import Session

from models import get_db_sync
from core.security import get_user_from_token, oauth2_scheme
from core.responses import (
    Forbidden,
    common_response,
    Ok,
    BadRequest,
    Unauthorized,
    InternalServerError,
)
from schemas.common import (
    BadRequestResponse,
    ForbiddenResponse,
    InternalServerErrorResponse,
    UnauthorizedResponse,
)
from schemas.payment import (
    CreatePaymentRequest,
    CreatePaymentResponse,
    DetailPaymentResponse,
    PaymentListResponse,
    Ticket,
    User,
)
from repository import payment as paymentRepo, ticket as ticketRepo
from core.mayar_service import MayarService
from models.Payment import PaymentStatus
from settings import (
    MAYAR_API_KEY,
    MAYAR_BASE_URL,
    MAYAR_WEBHOOK_SECRET,
)
from core.log import logger

router = APIRouter(prefix="/payment", tags=["Payment"])


@router.post(
    "/",
    responses={
        "200": {"model": CreatePaymentResponse},
        "400": {"model": BadRequestResponse},
        "401": {"model": UnauthorizedResponse},
        "500": {"model": InternalServerErrorResponse},
    },
)
async def create_payment(
    request: CreatePaymentRequest,
    db: Session = Depends(get_db_sync),
    token: str = Depends(oauth2_scheme),
):
    try:
        user = get_user_from_token(db=db, token=token)
        if user is None:
            return common_response(Unauthorized(message="Unauthorized"))

        if not user.email:
            return common_response(
                BadRequest(
                    message="Users must complete their email address first. Please update your profile."
                )
            )

        if not user.phone:
            return common_response(
                BadRequest(
                    message="Users must complete their phone number first. Please update your profile."
                )
            )

        ticket = ticketRepo.get_active_ticket_by_id(db=db, ticket_id=request.ticket_id)
        if not ticket:
            db.rollback()
            return common_response(BadRequest(message="Ticket not found."))

        if ticket.is_sold_out:
            db.rollback()
            return common_response(BadRequest(message="Ticket is sold out."))

        amount = ticket.price
        description = ticket.description or ticket.name

        payment = paymentRepo.create_payment(
            db=db,
            user_id=str(user.id),
            amount=amount,
            ticket_id=str(ticket.id),
            description=description,
            status=PaymentStatus.UNPAID,
            is_commit=False,
        )

        mayar_service = MayarService(api_key=MAYAR_API_KEY, base_url=MAYAR_BASE_URL)

        try:
            customer_name = user.username
            if user.first_name or user.last_name:
                customer_name = (
                    f"{user.first_name or ''} {user.last_name or ''}".strip()
                )

            mayar_response = await mayar_service.create_payment(
                ticket=ticket,
                customer_email=user.email,
                customer_name=customer_name,
                customer_phone=user.phone,
                tx_internal_id=str(payment.id),
            )

            data = mayar_response.get("data", {})
            payment_link = data.get("link", "")
            mayar_id = data.get("id", "")
            mayar_transaction_id = data.get("transactionId", "")
        except Exception as e:
            db.rollback()
            logger.error(f"Error creating payment in Mayar: {e}")
            return common_response(
                InternalServerError(
                    error="Failed to make a payment on Mayar. Please try again."
                )
            )

        paymentRepo.update_payment(
            db=db,
            payment=payment,
            payment_link=payment_link,
            mayar_id=mayar_id,
            mayar_transaction_id=mayar_transaction_id,
        )

        db.commit()
        db.refresh(payment)

        return common_response(
            Ok(
                data=CreatePaymentResponse(
                    id=str(payment.id),
                    payment_link=payment.payment_link,
                    created_at=payment.created_at,
                    amount=payment.amount,
                    description=payment.description,
                    ticket=Ticket(
                        id=str(ticket.id),
                        name=ticket.name,
                    ),
                ).model_dump(mode="json")
            )
        )
    except Exception as e:
        db.rollback()
        traceback.print_exc()
        logger.error(f"Error in create_payment: {e}")
        return common_response(InternalServerError(error="Internal Server Error"))


@router.get(
    "/",
    responses={
        "200": {"model": PaymentListResponse},
        "401": {"model": UnauthorizedResponse},
        "500": {"model": InternalServerErrorResponse},
    },
)
async def list_payments(
    db: Session = Depends(get_db_sync),
    token: str = Depends(oauth2_scheme),
):
    try:
        user = get_user_from_token(db=db, token=token)
        if user is None:
            return common_response(Unauthorized(message="Unauthorized"))

        payments = paymentRepo.get_payments_by_user_id(db=db, user_id=str(user.id))

        results = [
            DetailPaymentResponse(
                id=str(payment.id),
                user=User(
                    id=str(user.id),
                    first_name=user.first_name,
                    last_name=user.last_name,
                ),
                payment_link=payment.payment_link,
                status=payment.status,
                created_at=payment.created_at,
                paid_at=payment.paid_at,
                closed_at=payment.closed_at,
                amount=payment.amount,
                description=payment.description,
                ticket=Ticket(
                    id=str(payment.ticket.id),
                    name=payment.ticket.name,
                ),
            )
            for payment in payments
        ]

        return common_response(
            Ok(data=PaymentListResponse(results=results).model_dump(mode="json"))
        )
    except Exception as e:
        traceback.print_exc()
        logger.error(f"Error in list_payments: {e}")
        return common_response(
            InternalServerError(error=f"Internal Server Error: {str(e)}")
        )


@router.get(
    "/{payment_id}",
    responses={
        "200": {"model": DetailPaymentResponse},
        "400": {"model": BadRequestResponse},
        "401": {"model": UnauthorizedResponse},
        "403": {"model": ForbiddenResponse},
        "500": {"model": InternalServerErrorResponse},
    },
)
async def get_payment_detail(
    payment_id: str,
    db: Session = Depends(get_db_sync),
    token: str = Depends(oauth2_scheme),
):
    try:
        user = get_user_from_token(db=db, token=token)
        if user is None:
            return common_response(Unauthorized(message="Unauthorized"))

        payment = paymentRepo.get_payment_by_id(db=db, payment_id=payment_id)

        if not payment:
            return common_response(BadRequest(message="Payment not found"))

        if str(payment.user_id) != str(user.id):
            return common_response(
                Forbidden(
                    custom_response={
                        "message": "You do not have access to this payment"
                    }
                )
            )

        mayar_service = MayarService(api_key=MAYAR_API_KEY, base_url=MAYAR_BASE_URL)
        try:
            if payment.mayar_id and payment.status != PaymentStatus.PAID:
                mayar_status_response = await mayar_service.get_payment_status(
                    payment_id=payment.mayar_id
                )
                data = mayar_status_response.get("data", {})
                transaction_status = data.get("status", "").lower()

                status_mapping = {
                    "unpaid": PaymentStatus.UNPAID,
                    "paid": PaymentStatus.PAID,
                    "closed": PaymentStatus.CLOSED,
                }
                status = status_mapping.get(transaction_status, PaymentStatus.UNPAID)

                if status != payment.status:
                    paymentRepo.update_payment(
                        db=db,
                        payment=payment,
                        status=status,
                    )
                    db.commit()
                    db.refresh(payment)
        except Exception as e:
            logger.error(f"Error fetching payment status from Mayar: {e}")

        return common_response(
            Ok(
                data=DetailPaymentResponse(
                    id=str(payment.id),
                    user=User(
                        id=str(user.id),
                        first_name=user.first_name,
                        last_name=user.last_name,
                    ),
                    payment_link=payment.payment_link,
                    status=payment.status,
                    created_at=payment.created_at,
                    paid_at=payment.paid_at,
                    closed_at=payment.closed_at,
                    amount=payment.amount,
                    description=payment.description,
                    ticket=Ticket(
                        id=str(payment.ticket.id),
                        name=payment.ticket.name,
                    ),
                ).model_dump(mode="json")
            )
        )

    except Exception as e:
        traceback.print_exc()
        logger.error(f"Error in get_payment_detail: {e}")
        return common_response(
            InternalServerError(error=f"Internal Server Error: {str(e)}")
        )


@router.post(
    "/webhook",
    responses={
        "200": {"description": "Webhook processed successfully"},
        "400": {"model": BadRequestResponse},
        "500": {"model": InternalServerErrorResponse},
    },
)
async def payment_webhook(
    request: dict,
    db: Session = Depends(get_db_sync),
    x_callback_token: str = Header(None, alias="x-callback-token"),
):
    try:
        if not x_callback_token:
            return common_response(
                BadRequest(message="Missing X-Callback-Token header")
            )

        if x_callback_token != MAYAR_WEBHOOK_SECRET:
            return common_response(BadRequest(message="Invalid request token"))

        event = request.get("event")
        data = request.get("data", {})
        if event == "payment.received" and data:
            mayar_id = data.get("id")
            mayar_transaction_id = data.get("transactionId")
            transaction_status = data.get("status", "").lower()

            if not mayar_id and not mayar_transaction_id:
                return common_response(
                    BadRequest(message="id or transactionId is required")
                )

            status_mapping = {"success": PaymentStatus.PAID}

            status = status_mapping.get(transaction_status, PaymentStatus.UNPAID)

            payment = None
            if mayar_transaction_id:
                payment = paymentRepo.get_payment_by_mayar_transaction_id(
                    db=db, mayar_transaction_id=mayar_transaction_id
                )

            if not payment and mayar_id:
                payment = paymentRepo.get_payment_by_mayar_id(db=db, mayar_id=mayar_id)

            if not payment:
                logger.warning(
                    f"Payment not found for mayar_id: {mayar_id}, transactionId: {mayar_transaction_id}"
                )
                return common_response(BadRequest(message="Payment not found"))

            paymentRepo.update_payment(
                db=db,
                payment=payment,
                status=status,
                mayar_id=mayar_id,
                mayar_transaction_id=mayar_transaction_id,
            )

            logger.info(f"Payment {payment.id} updated to status {status} via webhook")

        return common_response(Ok(data={"message": "Webhook processed successfully"}))
    except Exception as e:
        traceback.print_exc()
        logger.error(f"Error in payment_webhook: {e}")
        return common_response(
            InternalServerError(error=f"Internal Server Error: {str(e)}")
        )
