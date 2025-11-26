"""
Script to create an admin user for the Recon API
"""
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.deps import SessionLocal
from app.auth.models import User
from app.auth.utils import create_user


def create_admin():
    """Create admin user"""
    db = SessionLocal()
    
    try:
        # Check if admin already exists
        existing_admin = db.query(User).filter(User.username == "admin").first()
        if existing_admin:
            print("❌ Admin user already exists!")
            print(f"   Username: {existing_admin.username}")
            print(f"   Email: {existing_admin.email}")
            print(f"   Created: {existing_admin.created_at}")
            return
        
        # Get user input
        print("=" * 50)
        print("CREATE ADMIN USER")
        print("=" * 50)
        
        username = input("Username [admin]: ").strip() or "admin"
        email = input("Email [admin@example.com]: ").strip() or "admin@example.com"
        password = input("Password [admin123]: ").strip() or "admin123"
        full_name = input("Full Name [Administrator]: ").strip() or "Administrator"
        
        # Create user
        print("\nCreating admin user...")
        user = create_user(
            db=db,
            username=username,
            email=email,
            password=password,
            full_name=full_name
        )
        
        # Make admin
        user.is_admin = True
        db.commit()
        
        print("\n✅ Admin user created successfully!")
        print(f"   Username: {user.username}")
        print(f"   Email: {user.email}")
        print(f"   Full Name: {user.full_name}")
        print(f"   Is Admin: {user.is_admin}")
        print(f"   Created: {user.created_at}")
        print("\n⚠️  IMPORTANT: Change the default password after first login!")
        
    except Exception as e:
        print(f"\n❌ Error creating admin user: {e}")
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    create_admin()

