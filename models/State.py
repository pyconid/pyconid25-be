from models import Base
from sqlalchemy import String, Integer, ForeignKey
from sqlalchemy.orm import mapped_column, Mapped, relationship


class State(Base):
    __tablename__ = "state"

    id: Mapped[int] = mapped_column(
        "id", Integer, primary_key=True, index=True, autoincrement=False
    )
    name: Mapped[str] = mapped_column("name", String(255), nullable=False, index=True)
    country_id: Mapped[int] = mapped_column(
        "country_id", Integer, ForeignKey("country.id"), nullable=False, index=True
    )
    country_code: Mapped[str] = mapped_column("country_code", String(2), nullable=True)
    fips_code: Mapped[str] = mapped_column("fips_code", String(255), nullable=True)
    iso2: Mapped[str] = mapped_column("iso2", String(255), nullable=True)
    type: Mapped[str] = mapped_column("type", String(191), nullable=True)
    latitude: Mapped[str] = mapped_column("latitude", String(20), nullable=True)
    longitude: Mapped[str] = mapped_column("longitude", String(20), nullable=True)

    # Relationships
    country = relationship("Country", back_populates="states")
    cities = relationship("City", back_populates="state")
    users = relationship("User", back_populates="state")
