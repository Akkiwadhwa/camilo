from extensions import db
from models import User
from application import app  # Make sure app is created before this runs

def create_admin():
    with app.app_context():
        db.create_all()
        username = input("Enter admin username: ").strip()
        password = input("Enter admin password: ").strip()

        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            print(f"User '{username}' already exists.")
        else:
            admin = User(username=username, is_admin=True)
            admin.set_password(password)
            db.session.add(admin)
            db.session.commit()
            print(f"Admin user '{username}' created successfully.")

if __name__ == "__main__":
    create_admin()
