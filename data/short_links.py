from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from data.db_session import SqlAlchemyBase

class ShortLink(SqlAlchemyBase):
    __tablename__ = 'short_links'

    id = Column(Integer, primary_key=True, autoincrement=True)
    original_url = Column(String, nullable=False)
    short_code = Column(String, unique=True, nullable=False)
    created_at = Column(DateTime, nullable=False)
    expired_at = Column(DateTime, nullable=False)
    is_active = Column(Boolean, default=True)
    clicks = Column(Integer, default=0)

    user_id = Column(Integer, ForeignKey("users.id"))
    user = relationship("Users")
