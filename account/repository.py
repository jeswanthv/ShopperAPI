import bcrypt
from sqlalchemy.orm import Session
from . import models


class AccountRepository:

    def hash_password(self, password: str) -> str:
        """Hashes a password and returns it as a string."""
        pwd_bytes = password.encode('utf-8')
        salt = bcrypt.gensalt()
        hashed_bytes = bcrypt.hashpw(password=pwd_bytes, salt=salt)
        return hashed_bytes.decode('utf-8')  # Decode to string for DB storage

    def verify_password(self, plain_password: str, hashed_password_str: str) -> bool:
        """Verifies a plain password against a hashed password string from the DB."""
        plain_bytes = plain_password.encode('utf-8')
        hashed_bytes = hashed_password_str.encode('utf-8')
        return bcrypt.checkpw(plain_bytes, hashed_bytes)

    def get_account_by_email(self, db: Session, email: str):
        return db.query(models.Account).filter(models.Account.email == email).first()

    def get_account_by_id(self, db: Session, user_id: int):
        return db.query(models.Account).filter(models.Account.id == user_id).first()

    def create_account(self, db: Session, name: str, email: str, password: str):
        hashed_password_str = self.hash_password(
            password)  # Use the new function
        db_account = models.Account(
            name=name,
            email=email,
            password=hashed_password_str  # Store the string hash
        )
        db.add(db_account)
        db.commit()
        db.refresh(db_account)
        return db_account
