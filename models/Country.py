from models import Base
from sqlalchemy import String, Integer, JSON
from sqlalchemy.orm import mapped_column, Mapped, relationship


class Country(Base):
    __tablename__ = "country"

    id: Mapped[int] = mapped_column(
        "id", Integer, primary_key=True, index=True, autoincrement=False
    )
    name: Mapped[str] = mapped_column("name", String(100), nullable=False, index=True)
    iso3: Mapped[str] = mapped_column("iso3", String(3), nullable=True)
    iso2: Mapped[str] = mapped_column("iso2", String(2), nullable=True, index=True)
    numeric_code: Mapped[str] = mapped_column("numeric_code", String(3), nullable=True)
    phone_code: Mapped[str] = mapped_column("phone_code", String(255), nullable=True)
    capital: Mapped[str] = mapped_column("capital", String(255), nullable=True)
    currency: Mapped[str] = mapped_column("currency", String(255), nullable=True)
    currency_name: Mapped[str] = mapped_column(
        "currency_name", String(255), nullable=True
    )
    currency_symbol: Mapped[str] = mapped_column(
        "currency_symbol", String(255), nullable=True
    )
    tld: Mapped[str] = mapped_column("tld", String(255), nullable=True)
    native: Mapped[str] = mapped_column("native", String(255), nullable=True)
    region: Mapped[str] = mapped_column("region", String(255), nullable=True)
    subregion: Mapped[str] = mapped_column("subregion", String(255), nullable=True)
    nationality: Mapped[str] = mapped_column("nationality", String(255), nullable=True)
    timezones: Mapped[str] = mapped_column("timezones", JSON, nullable=True)
    translations: Mapped[str] = mapped_column("translations", JSON, nullable=True)
    latitude: Mapped[str] = mapped_column("latitude", String(20), nullable=True)
    longitude: Mapped[str] = mapped_column("longitude", String(20), nullable=True)
    emoji: Mapped[str] = mapped_column("emoji", String(191), nullable=True)
    emojiU: Mapped[str] = mapped_column("emojiU", String(191), nullable=True)

    # Relationships
    states = relationship("State", back_populates="country")
    users = relationship("User", back_populates="country")
