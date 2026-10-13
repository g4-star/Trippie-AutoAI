from datetime import datetime

from sqlalchemy import DateTime, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class GmailOAuthTransaction(Base):
    __tablename__ = "gmail_oauth_transactions"

    state: Mapped[str] = mapped_column(String(255), primary_key=True)
    redirect_uri: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.utcnow
    )
