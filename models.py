from datetime import date
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class Client(db.Model):
    __tablename__ = "clients"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    address = db.Column(db.Text, nullable=False, default="")
    phone = db.Column(db.String(30), nullable=False, default="")
    created_at = db.Column(db.Date, nullable=False, default=date.today)
    receipts = db.relationship("Receipt", backref="client", lazy="dynamic", cascade="all, delete-orphan")

    def to_dict(self):
        return dict(id=self.id, name=self.name, address=self.address, phone=self.phone)


class Receipt(db.Model):
    __tablename__ = "receipts"
    id = db.Column(db.Integer, primary_key=True)
    receipt_number = db.Column(db.String(40), nullable=False, unique=True)
    batch_id = db.Column(db.String(10), nullable=False, index=True)
    client_id = db.Column(db.Integer, db.ForeignKey("clients.id"), nullable=False)
    truck_no = db.Column(db.String(50), nullable=False)
    from_loc = db.Column(db.String(200), nullable=False)
    to_loc = db.Column(db.String(200), nullable=False)
    num_trips = db.Column(db.Integer, nullable=False)
    rate_per_trip = db.Column(db.Float, nullable=False)
    total = db.Column(db.Float, nullable=False)
    invoice_date = db.Column(db.Date, nullable=False, default=date.today)
    trip_date = db.Column(db.Date, nullable=False, default=date.today)
    printed = db.Column(db.Boolean, nullable=False, default=False)

    def to_dict(self):
        return dict(
            id=self.id,
            receipt_number=self.receipt_number,
            batch_id=self.batch_id,
            client=self.client.to_dict() if self.client else None,
            truck_no=self.truck_no,
            from_loc=self.from_loc,
            to_loc=self.to_loc,
            num_trips=self.num_trips,
            rate_per_trip=self.rate_per_trip,
            total=self.total,
            invoice_date=self.invoice_date.isoformat(),
            trip_date=self.trip_date.isoformat(),
            printed=self.printed,
        )
