from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.db.models import Base
from config.settings import DATABASE_URL


replica_engine = create_engine(DATABASE_URL, pool_pre_ping=True)
ReplicaSession = sessionmaker(bind=replica_engine)


def init_db():
    # This will create the 'products' and 'interactions' tables
    Base.metadata.create_all(replica_engine)


# Run this once to create the tables
if __name__ == "__main__":
    print("Initializing recommender database...")
    init_db()
    print("Database initialized.")
