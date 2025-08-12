from app import create_app
from app.models import db

app = create_app()

with app.app_context():
    # Drop all tables and recreate them
    db.drop_all()
    db.create_all()
    print("Database initialized successfully!")
    print("Tables created:")
    for table in db.metadata.tables.keys():
        print(f"  - {table}")