from sqlalchemy.orm import Session
from sqlalchemy import select


def initialize_checkin_data(
    db: Session,
):
    import uuid

    from models.User import User
    from models.Ticket import Ticket
    from models.Payment import Payment, PaymentStatus
    from core.security import generate_hash_password
    from core.helper import get_current_time_in_timezone

    ticket_id = uuid.UUID("550e8400-e29b-41d4-a716-446655440000")
    payment_id = uuid.UUID("550e8400-e29b-41d4-a716-446655440001")
    user_id = uuid.UUID("550e8400-e29b-41d4-a716-446655440002")

    # Check if data already exists
    existing_user = db.execute(
        select(User).where(User.id == user_id)
    ).scalar_one_or_none()
    existing_ticket = db.execute(
        select(Ticket).where(Ticket.id == ticket_id)
    ).scalar_one_or_none()
    existing_payment = db.execute(
        select(Payment).where(Payment.id == payment_id)
    ).scalar_one_or_none()

    if existing_user and existing_ticket and existing_payment:
        print("All checkin data already exists. Skipping...")
        return

    try:
        if not existing_user:
            user = User(
                id=user_id,
                username="checkinuser",
                email="checkinuser@example.com",
                phone="+628123456789",
                first_name="test",
                last_name="user",
                password=generate_hash_password("password"),
                is_active=True,
            )
            db.add(user)
        else:
            user = existing_user

        if not existing_ticket:
            ticket = Ticket(
                id=ticket_id,
                name="Test Conference Ticket",
                price=500000,
                user_participant_type="In Person",
                is_sold_out=False,
                is_active=True,
                description="Test ticket for payment",
            )
            db.add(ticket)
        else:
            ticket = existing_ticket

        if not existing_payment:
            payment = Payment(
                id=payment_id,
                user_id=user.id,
                ticket_id=ticket.id,
                payment_link="https://mayar.id/pay/test-link",
                status=PaymentStatus.PAID,
                created_at=get_current_time_in_timezone(),
                mayar_id="mayar-test-id",
                mayar_transaction_id="mayar-test-tx",
                amount=500000,
                description="Test payment",
            )
            db.add(payment)
        else:
            payment = existing_payment

        db.commit()
        db.refresh(user)
        db.refresh(ticket)
        db.refresh(payment)
        print("Checkin data initialized successfully!")
    except Exception as e:
        db.rollback()
        print(f"Error initializing checkin data: {e}")
        raise
