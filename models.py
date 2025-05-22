from extensions import db
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)
    # Script permissions
    can_access_script1 = db.Column(db.Boolean, default=False)
    can_access_script2 = db.Column(db.Boolean, default=False)
    can_access_script3 = db.Column(db.Boolean, default=False)
    can_access_script4 = db.Column(db.Boolean, default=False)
    can_access_script5 = db.Column(db.Boolean, default=False)
    # Relationship with files
    files = db.relationship('File', backref='owner', lazy=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class File(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(255), nullable=False)
    original_filename = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    script_type = db.Column(db.String(50), nullable=False)  # To track which script generated the file
