"""
models.py — Database models for the Vendor Management System
"""

# Import SQLAlchemy: The main database library for Flask
from flask_sqlalchemy import SQLAlchemy
# Import UserMixin: Provides default implementations for Flask-Login (e.g. is_authenticated)
from flask_login import UserMixin
# Import hashing tools: generate_password_hash (save) and check_password_hash (verify)
from werkzeug.security import generate_password_hash, check_password_hash

# Initialize the db object: This will be used in app.py to connect to the database
db = SQLAlchemy()


class User(UserMixin, db.Model):
    """System users (officers who log in)."""
    __tablename__ = 'users' # Name of the table in the SQL database

    # Primary key: Unique ID for every user record
    id       = db.Column(db.Integer, primary_key=True)
    # Unique username used for logging in
    username = db.Column(db.String(80),  unique=True, nullable=False)
    # Unique email for communication and identification
    email    = db.Column(db.String(120), unique=True, nullable=False)
    # Hashed password (never store plain text passwords!)
    password_hash = db.Column(db.String(200), nullable=False)
    # Role: admin, field_officer, finance_officer, or vendor
    role          = db.Column(db.String(30), default='field_officer')
    # Link to Vendor table: If this user is a vendor, this points to their data
    vendor_ptr    = db.Column(db.Integer, db.ForeignKey('vendors.id'), nullable=True)
    # When the account was created
    created_at    = db.Column(db.String(30), default='')

    def set_password(self, password):
        """Hashes the password and saves it to the database."""
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        """Compares a plain password with the stored hash to verify login."""
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        """String representation: shows when debugging code."""
        return f'<User {self.username}>'


class Street(db.Model):
    """Normalized street/zone names."""
    __tablename__ = 'streets'
    # Unique street identifier
    id   = db.Column(db.Integer, primary_key=True)
    # Street name
    name = db.Column(db.String(100), unique=True, nullable=False)

    def __repr__(self):
        """String representation of street."""
        return f'<Street {self.name}>'


class Vendor(db.Model):
    """Street vendor record."""
    __tablename__ = 'vendors'

    # Primary key for vendor
    id           = db.Column(db.Integer, primary_key=True)
    # Unique public ID (e.g. VND-001)
    vendor_id    = db.Column(db.String(20),  unique=True, nullable=False)
    # Full legal name of the vendor
    full_name    = db.Column(db.String(100), nullable=False)
    # Vendor contact phone number
    phone        = db.Column(db.String(20),  nullable=False)
    # National ID Number
    nin          = db.Column(db.String(30),  default='')
    # Date of birth
    dob          = db.Column(db.String(20),  default='')
    # Foreign key to Streets table
    street_id    = db.Column(db.Integer, db.ForeignKey('streets.id'), nullable=True)
    # Legacy support / fallback for street name
    street       = db.Column(db.String(100), nullable=True)
    # Trade type category
    trade_type   = db.Column(db.String(60),  nullable=False)
    # Allocated stall number
    stall_number = db.Column(db.String(20),  default='')
    # Start date of the permit
    permit_start = db.Column(db.String(20),  default='')
    # Expiry date of the permit
    permit_end   = db.Column(db.String(20),  default='')
    # Current status: Active | Pending | Expired | NotPaid
    status       = db.Column(db.String(20),  default='Active')
    # Internal admin notes
    notes        = db.Column(db.Text,        default='')
    # Timestamp of registration
    registered_at = db.Column(db.String(30), default='')

    # Relationships: Allow access to related data
    # List of all receipts for this vendor
    receipts     = db.relationship('Receipt', backref='vendor_ref', lazy=True)
    # List of all fee payments for this vendor
    fee_payments  = db.relationship('FeePayment', backref='vendor_ref', lazy=True)
    # Link to the street object
    street_ref   = db.relationship('Street', backref='vendors', lazy=True)

    def to_dict(self):
        """Converts the object to a dictionary for JSON responses."""
        return {
            'id':          self.id,
            'vendor_id':   self.vendor_id,
            'full_name':   self.full_name,
            'phone':       self.phone,
            'street':      self.street_ref.name if self.street_ref else self.street,
            'trade_type':  self.trade_type,
            'status':      self.status,
            'permit_end':  self.permit_end,
        }

    def __repr__(self):
        return f'<Vendor {self.vendor_id} – {self.full_name}>'


class Fine(db.Model):
    """Fines assigned to street vendors."""
    __tablename__ = 'fines'
    
    id          = db.Column(db.Integer, primary_key=True)
    vendor_id   = db.Column(db.Integer, db.ForeignKey('vendors.id'), nullable=False)
    amount      = db.Column(db.Float, nullable=False)
    reason      = db.Column(db.String(200), nullable=False)
    date_issued = db.Column(db.String(30), nullable=False)
    status      = db.Column(db.String(20), default='Unpaid') # Unpaid | Paid
    issued_by   = db.Column(db.String(80), nullable=False)
    
    vendor_ref  = db.relationship('Vendor', backref=db.backref('fines', lazy=True))



class FeeSchedule(db.Model):
    """Definitions of fees (Daily, Weekly, etc.)."""
    __tablename__ = 'fee_schedules'
    id        = db.Column(db.Integer, primary_key=True)
    name      = db.Column(db.String(60), nullable=False) # e.g. "Daily Pitch Fee"
    amount    = db.Column(db.Float,      nullable=False)
    frequency = db.Column(db.String(20), nullable=False) # daily | weekly

    def __repr__(self):
        return f'<FeeSchedule {self.name} - {self.frequency}>'


class FeePayment(db.Model):
    """Tracking record for vendor fee payments."""
    __tablename__ = 'fee_payments'
    id          = db.Column(db.Integer, primary_key=True)
    vendor_id   = db.Column(db.Integer, db.ForeignKey('vendors.id'), nullable=False)
    schedule_id = db.Column(db.Integer, db.ForeignKey('fee_schedules.id'), nullable=False)
    period_date = db.Column(db.String(20),  nullable=False) # e.g. "2026-04-27" or "2026-W17"
    paid_date   = db.Column(db.String(30),  nullable=True)
    status      = db.Column(db.String(20),  default='Unpaid') # Paid | Unpaid | Overdue
    receipt_id  = db.Column(db.Integer, db.ForeignKey('receipts.id'), nullable=True)

    schedule_ref = db.relationship('FeeSchedule', backref='payments', lazy=True)
    receipt_ref  = db.relationship('Receipt', backref='fee_payment', lazy=True)

    def __repr__(self):
        return f'<FeePayment {self.vendor_id} - {self.period_date} - {self.status}>'


class Receipt(db.Model):
    """Fee receipt issued to a vendor."""
    __tablename__ = 'receipts'

    id          = db.Column(db.Integer, primary_key=True)
    receipt_no  = db.Column(db.String(20), unique=True, nullable=False)  # e.g. RCP-0001
    vendor_id   = db.Column(db.Integer, db.ForeignKey('vendors.id'), nullable=False)
    fee_type    = db.Column(db.String(60),  nullable=False)
    amount      = db.Column(db.Float,       nullable=False)
    date_issued = db.Column(db.String(30),  nullable=False)
    issued_by   = db.Column(db.String(80),  default='')
    notes       = db.Column(db.Text,        default='')
    status      = db.Column(db.String(20),  default='Paid')  # Paid | Overdue | Cancelled
    is_verified = db.Column(db.Boolean,     default=False)
    verified_by = db.Column(db.String(80),  nullable=True)
    verified_at = db.Column(db.String(30),  nullable=True)

    def __repr__(self):
        return f'<Receipt {self.receipt_no}>'
