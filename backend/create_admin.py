import sys
import getpass
from sqlalchemy.orm import Session
from passlib.context import CryptContext
from models import User, get_db, Base, engine

# Ensure tables exist
Base.metadata.create_all(bind=engine)

pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")

def create_superuser():
    print("\n🛡️  AegisAI Root Admin Setup Tool 🛡️")
    print("-" * 35)
    
    email = input("Admin Email: ").strip()
    full_name = input("Admin Full Name: ").strip()
    password = getpass.getpass("Admin Password (Hidden): ")
    
    if len(password) < 8:
        print("❌ Error: Admin password must be at least 8 characters.")
        sys.exit(1)

    db = next(get_db())
    
    existing = db.query(User).filter(User.email == email).first()
    if existing:
        print(f"❌ Error: User with email '{email}' already exists.")
        sys.exit(1)
        
    hashed_pw = pwd_context.hash(password)
    
    # Create the user with is_admin explicitly set to True
    admin_user = User(
        email=email,
        full_name=full_name,
        hashed_password=hashed_pw,
        is_admin=True
    )
    
    db.add(admin_user)
    db.commit()
    print(f"\n✅ SUCCESS: Root admin '{email}' has been securely provisioned.")

if __name__ == "__main__":
    create_superuser()