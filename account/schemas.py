from pydantic import BaseModel, EmailStr


class AccountBase(BaseModel):
    name: str
    email: EmailStr


class Account(AccountBase):
    id: int

    class Config:
        from_attributes = True  # Tells Pydantic to read data from SQLAlchemy models
