from models import Base
from sqlalchemy import String, Integer, ForeignKey
from sqlalchemy.orm import mapped_column, Mapped, relationship


class City(Base):
    __tablename__ = "city"

    id: Mapped[int] = mapped_column(
        "id", Integer, primary_key=True, index=True, autoincrement=False
    )
    name: Mapped[str] = mapped_column("name", String(255), nullable=False, index=True)
    state_id: Mapped[int] = mapped_column(
        "state_id", Integer, ForeignKey("state.id"), nullable=False, index=True
    )
    state_code: Mapped[str] = mapped_column("state_code", String(255), nullable=True)
    country_id: Mapped[int] = mapped_column(
        "country_id", Integer, ForeignKey("country.id"), nullable=False, index=True
    )
    country_code: Mapped[str] = mapped_column("country_code", String(2), nullable=True)
    latitude: Mapped[str] = mapped_column("latitude", String(20), nullable=True)
    longitude: Mapped[str] = mapped_column("longitude", String(20), nullable=True)
    wikiDataId: Mapped[str] = mapped_column("wikiDataId", String(255), nullable=True)

    # Relationships
    state = relationship("State", back_populates="cities")
    country = relationship("Country")
    users = relationship("User", back_populates="city")
