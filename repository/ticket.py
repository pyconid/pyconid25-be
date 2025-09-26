from sqlalchemy.orm import Session
from models.Ticket import Ticket

def get_active_tickets(db: Session):
    return db.query(Ticket).filter(Ticket.is_active).all()