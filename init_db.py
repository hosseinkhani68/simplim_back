from database.database import Base, engine
from database.models import User, TextHistory, PDFDocument

def init_db():
    # Create all tables
    Base.metadata.create_all(bind=engine)
    print("Database tables created successfully!")

if __name__ == "__main__":
    init_db() 