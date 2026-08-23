import os
import uuid
from datetime import date, datetime

from flask import Flask, jsonify, render_template, request
from models import Client, Receipt, db


def parse_date(value, fallback=None):
    if fallback is None:
        fallback = date.today()
    if not value:
        return fallback
    try:
        return datetime.strptime(str(value).strip(), "%Y-%m-%d").date()
    except (TypeError, ValueError):
        return fallback

app = Flask(__name__, static_folder="static", template_folder="templates")
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL", "sqlite:///receipts.db")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db.init_app(app)

with app.app_context():
    db.create_all()


# ---------------------------------------------------------------------------
# Validation (kept compact)
# ---------------------------------------------------------------------------

def validate(data):
    if not isinstance(data, dict):
        return "", "", [], ["Invalid request payload."]
    client_name = str(data.get("clientName", "")).strip()
    client_address = str(data.get("clientAddress", "")).strip()
    errors = ([] if client_name else ["Client name is required."]) + ([] if client_address else ["Client address is required."])
    raw_trips = data.get("trips", [])
    if not isinstance(raw_trips, list) or not raw_trips:
        return client_name, client_address, [], errors + ["Add at least one trip row."]
    trips = []
    for number, row in enumerate(raw_trips, 1):
        truck = str(row.get("truckNo", "")).strip()
        origin = str(row.get("from", "")).strip()
        destination = str(row.get("to", "")).strip()
        trips_value = row.get("trips", "")
        rate_value = row.get("rate", "")
        if not any((truck, origin, destination, str(trips_value).strip(), str(rate_value).strip())):
            continue
        row_errors = []
        if not truck:
            row_errors.append("Truck number is required")
        if not origin:
            row_errors.append("From location is required")
        if not destination:
            row_errors.append("To location is required")
        try:
            count = int(trips_value)
            if count < 1:
                row_errors.append("Trips must be at least 1")
        except (TypeError, ValueError):
            count = 0
            row_errors.append("Trips must be a whole number")
        try:
            rate = float(rate_value)
            if rate < 0:
                row_errors.append("Rate must be zero or positive")
        except (TypeError, ValueError):
            rate = 0
            row_errors.append("Rate must be a number")
        errors.extend(f"Row {number}: {m}." for m in row_errors)
        if not row_errors:
            trips.append(dict(truck_no=truck, from_loc=origin, to_loc=destination,
                              num_trips=count, rate_per_trip=rate, total=count * rate,
                              trip_date=parse_date(row.get("tripDate"))))
    if not trips and not any(e.startswith("Row ") for e in errors):
        errors.append("Add at least one completed trip row.")
    return client_name, client_address, trips, errors


# ---------------------------------------------------------------------------
# Pages
# ---------------------------------------------------------------------------

@app.route("/")
def index():
    return render_template("index.html")


# ---------------------------------------------------------------------------
# Client API
# ---------------------------------------------------------------------------

@app.route("/api/clients", methods=["GET"])
def list_clients():
    clients = Client.query.order_by(Client.name).all()
    return jsonify(clients=[c.to_dict() for c in clients])


@app.route("/api/clients", methods=["POST"])
def create_client():
    data = request.get_json(silent=True) or {}
    name = str(data.get("name", "")).strip()
    address = str(data.get("address", "")).strip()
    phone = str(data.get("phone", "")).strip()
    if not name:
        return jsonify(success=False, errors=["Client name is required."]), 400
    client = Client(name=name, address=address, phone=phone)
    db.session.add(client)
    db.session.commit()
    return jsonify(success=True, client=client.to_dict())


@app.route("/api/clients/<int:client_id>", methods=["PUT"])
def update_client(client_id):
    client = Client.query.get_or_404(client_id)
    data = request.get_json(silent=True) or {}
    if "name" in data:
        client.name = str(data["name"]).strip()
    if "address" in data:
        client.address = str(data["address"]).strip()
    if "phone" in data:
        client.phone = str(data["phone"]).strip()
    db.session.commit()
    return jsonify(success=True, client=client.to_dict())


@app.route("/api/clients/<int:client_id>", methods=["DELETE"])
def delete_client(client_id):
    client = Client.query.get_or_404(client_id)
    db.session.delete(client)
    db.session.commit()
    return jsonify(success=True)


# ---------------------------------------------------------------------------
# Receipt generation + storage
# ---------------------------------------------------------------------------

def _find_or_create_client(name, address):
    """Reuse existing client if name matches, otherwise create."""
    client = Client.query.filter(db.func.lower(Client.name) == name.lower()).first()
    if client:
        if address and client.address != address:
            client.address = address
            db.session.commit()
        return client
    client = Client(name=name, address=address)
    db.session.add(client)
    db.session.commit()
    return client


@app.route("/generate_invoice", methods=["POST"])
def generate_invoice():
    raw = request.get_json(silent=True) or {}
    client_name, client_address, trips, errors = validate(raw)
    if errors:
        return jsonify(success=False, errors=errors), 400
    batch_id = uuid.uuid4().hex[:6].upper()
    client = _find_or_create_client(client_name, client_address)
    invoice_date = parse_date(raw.get("invoiceDate"))
    custom_receipt_number = str(raw.get("receiptNumber", "")).strip()
    # Save each trip as a receipt
    saved = []
    for i, t in enumerate(trips, 1):
        r = Receipt(
            receipt_number=f"{custom_receipt_number}-{i:03d}" if custom_receipt_number else f"INV-{batch_id}-{i:03d}",
            batch_id=batch_id,
            client_id=client.id,
            truck_no=t["truck_no"],
            from_loc=t["from_loc"],
            to_loc=t["to_loc"],
            num_trips=t["num_trips"],
            rate_per_trip=t["rate_per_trip"],
            total=t["total"],
            invoice_date=invoice_date,
            trip_date=t["trip_date"],
        )
        db.session.add(r)
        saved.append(r)
    db.session.commit()
    return jsonify(
        success=True,
        html=render_template(
            "invoice_fragment.html",
            document_number=custom_receipt_number or f"INV-{batch_id}",
            document_date=invoice_date.isoformat(),
            client_name=client.name,
            client_address=client.address,
            trips=trips,
            grand_total=sum(t["total"] for t in trips),
        ),
        receipt_ids=[r.id for r in saved],
    )


@app.route("/generate_receipts", methods=["POST"])
def generate_receipts():
    raw = request.get_json(silent=True) or {}
    client_name, client_address, trips, errors = validate(raw)
    if errors:
        return jsonify(success=False, errors=errors), 400
    batch_id = uuid.uuid4().hex[:6].upper()
    client = _find_or_create_client(client_name, client_address)
    invoice_date = parse_date(raw.get("invoiceDate"))
    custom_receipt_number = str(raw.get("receiptNumber", "")).strip()
    saved = []
    for i, t in enumerate(trips, 1):
        r = Receipt(
            receipt_number=f"{custom_receipt_number}-{i:03d}" if custom_receipt_number else f"RCP-{batch_id}-{i:03d}",
            batch_id=batch_id,
            client_id=client.id,
            truck_no=t["truck_no"],
            from_loc=t["from_loc"],
            to_loc=t["to_loc"],
            num_trips=t["num_trips"],
            rate_per_trip=t["rate_per_trip"],
            total=t["total"],
            invoice_date=invoice_date,
            trip_date=t["trip_date"],
        )
        db.session.add(r)
        saved.append(r)
    db.session.commit()
    return jsonify(
        success=True,
        html=render_template(
            "receipts_fragment.html",
            batch_id=custom_receipt_number or batch_id,
            receipt_date=invoice_date.isoformat(),
            client_name=client.name,
            client_address=client.address,
            trips=trips,
        ),
        count=len(trips),
        receipt_ids=[r.id for r in saved],
    )


# ---------------------------------------------------------------------------
# Saved receipts API
# ---------------------------------------------------------------------------

@app.route("/api/receipts", methods=["GET"])
def list_receipts():
    client_id = request.args.get("client_id", type=int)
    batch = request.args.get("batch_id", type=str)
    q = Receipt.query.order_by(Receipt.invoice_date.desc(), Receipt.id.desc())
    if client_id:
        q = q.filter_by(client_id=client_id)
    if batch:
        q = q.filter_by(batch_id=batch)
    receipts = q.all()
    return jsonify(receipts=[r.to_dict() for r in receipts])


@app.route("/api/receipts/batches", methods=["GET"])
def list_batches():
    """Group receipts by batch_id for easy batch management."""
    rows = db.session.query(
        Receipt.batch_id,
        db.func.min(Receipt.invoice_date),
        db.func.count(Receipt.id),
        db.func.sum(Receipt.total),
        Receipt.client_id,
    ).group_by(Receipt.batch_id).order_by(db.func.min(Receipt.invoice_date).desc()).all()
    batches = []
    for batch_id, rdate, count, total, cid in rows:
        client = Client.query.get(cid)
        batches.append(dict(
            batch_id=batch_id,
            date=rdate.isoformat() if rdate else "",
            count=count,
            total=round(total or 0, 2),
            client=client.to_dict() if client else None,
        ))
    return jsonify(batches=batches)


@app.route("/api/receipts/<int:receipt_id>", methods=["PUT"])
def update_receipt(receipt_id):
    r = Receipt.query.get_or_404(receipt_id)
    data = request.get_json(silent=True) or {}
    if "truck_no" in data:
        r.truck_no = str(data["truck_no"]).strip()
    if "from_loc" in data:
        r.from_loc = str(data["from_loc"]).strip()
    if "to_loc" in data:
        r.to_loc = str(data["to_loc"]).strip()
    if "num_trips" in data:
        r.num_trips = int(data["num_trips"])
    if "rate_per_trip" in data:
        r.rate_per_trip = float(data["rate_per_trip"])
    if "trip_date" in data:
        r.trip_date = parse_date(data["trip_date"])
    if "invoice_date" in data:
        r.invoice_date = parse_date(data["invoice_date"])
    r.total = r.num_trips * r.rate_per_trip
    db.session.commit()
    return jsonify(success=True, receipt=r.to_dict())


@app.route("/api/receipts/<int:receipt_id>", methods=["DELETE"])
def delete_receipt(receipt_id):
    r = Receipt.query.get_or_404(receipt_id)
    db.session.delete(r)
    db.session.commit()
    return jsonify(success=True)


@app.route("/api/receipts/batch/<batch_id>", methods=["DELETE"])
def delete_batch(batch_id):
    Receipt.query.filter_by(batch_id=batch_id).delete()
    db.session.commit()
    return jsonify(success=True)


# ---------------------------------------------------------------------------
# Batch print
# ---------------------------------------------------------------------------

@app.route("/api/receipts/batch/<batch_id>/print", methods=["GET"])
def print_batch(batch_id):
    receipts = Receipt.query.filter_by(batch_id=batch_id).order_by(Receipt.id).all()
    if not receipts:
        return "No receipts found for this batch.", 404
    mode = request.args.get("mode", "multi")  # "single" or "multi"
    receipt_number_override = request.args.get("receipt_number", "").strip()
    client = receipts[0].client
    trips = [dict(truck_no=r.truck_no, from_loc=r.from_loc, to_loc=r.to_loc,
                  num_trips=r.num_trips, rate_per_trip=r.rate_per_trip, total=r.total,
                  trip_date=r.trip_date.isoformat())
             for r in receipts]
    grand_total = sum(t["total"] for t in trips)
    is_invoice = receipts[0].receipt_number.startswith("INV")
    if is_invoice:
        html = render_template(
            "invoice_fragment.html",
            document_number=receipt_number_override or f"INV-{batch_id}",
            document_date=receipts[0].invoice_date.isoformat(),
            client_name=client.name,
            client_address=client.address,
            trips=trips,
            grand_total=grand_total,
        )
    elif mode == "single":
        html = render_template(
            "receipt_single_fragment.html",
            document_number=receipt_number_override or f"RCP-{batch_id}",
            receipt_date=receipts[0].invoice_date.isoformat(),
            client_name=client.name,
            client_address=client.address,
            trips=trips,
            grand_total=grand_total,
        )
    else:
        html = render_template(
            "receipts_fragment.html",
            batch_id=receipt_number_override or batch_id,
            receipt_date=receipts[0].invoice_date.isoformat(),
            client_name=client.name,
            client_address=client.address,
            trips=trips,
            grand_total=grand_total,
        )
    return html


@app.route("/print_batch_page/<batch_id>", methods=["GET"])
def print_batch_page(batch_id):
    """Full page wrapper for printing a batch."""
    if batch_id == "multi":
        return render_template("multi_print.html")
    return render_template("print_page.html", batch_id=batch_id)


# ---------------------------------------------------------------------------
# Custom multi-batch print (user picks receipts from different batches)
# ---------------------------------------------------------------------------

@app.route("/api/receipts/multi_print", methods=["POST"])
def multi_print():
    """Accept list of receipt IDs, render all as a single print page."""
    data = request.get_json(silent=True) or {}
    ids = data.get("receipt_ids", [])
    mode = data.get("mode", "multi")  # "single" or "multi"
    receipt_number_override = str(data.get("receipt_number", "")).strip()
    if not ids:
        return jsonify(success=False, errors=["Select at least one receipt."]), 400
    receipts = Receipt.query.filter(Receipt.id.in_(ids)).order_by(Receipt.id).all()
    trips = [dict(truck_no=r.truck_no, from_loc=r.from_loc, to_loc=r.to_loc,
                  num_trips=r.num_trips, rate_per_trip=r.rate_per_trip, total=r.total,
                  trip_date=r.trip_date.isoformat(),
                  client_name=r.client.name if r.client else "",
                  client_address=r.client.address if r.client else "")
             for r in receipts]
    grand_total = sum(t["total"] for t in trips)
    # Use the first receipt's client info for the single-receipt header
    first_client = receipts[0].client if receipts else None
    if mode == "single":
        html = render_template(
            "receipt_single_fragment.html",
            document_number=receipt_number_override or "RCP-MULTI",
            receipt_date=date.today().isoformat(),
            client_name=first_client.name if first_client else "",
            client_address=first_client.address if first_client else "",
            trips=trips,
            grand_total=grand_total,
        )
    else:
        html = render_template(
            "receipts_fragment.html",
            batch_id=receipt_number_override or "MULTI",
            receipt_date=date.today().isoformat(),
            client_name="",
            client_address="",
            trips=trips,
            grand_total=grand_total,
        )
    return jsonify(success=True, html=html)


# ---------------------------------------------------------------------------
# Seed demo data (optional, for first run)
# ---------------------------------------------------------------------------

@app.route("/api/seed", methods=["POST"])
def seed_demo():
    """Add sample clients and receipts for quick testing."""
    if Client.query.count() > 0:
        return jsonify(success=False, message="Data already exists.")
    clients_data = [
        ("Rajendra Jagtap", "Hinjewadi, Pune", "9876543210"),
        ("Suresh Patil", "Baner, Pune", "9123456780"),
        ("Anil Deshmukh", "Wakad, Pune", "9988776655"),
    ]
    created = []
    for name, addr, phone in clients_data:
        c = Client(name=name, address=addr, phone=phone)
        db.session.add(c)
        created.append(c)
    db.session.flush()
    batch_id = uuid.uuid4().hex[:6].upper()
    sample = [
        (created[0].id, "MH 12 AB 1234", "Pune", "Mumbai", 3, 1500),
        (created[0].id, "MH 12 AB 1234", "Pune", "Nashik", 2, 2000),
        (created[1].id, "MH 14 CD 5678", "Pune", "Satara", 5, 1200),
    ]
    today = date.today()
    for i, (cid, truck, fr, to, trips, rate) in enumerate(sample, 1):
        r = Receipt(
            receipt_number=f"RCP-{batch_id}-{i:03d}",
            batch_id=batch_id,
            client_id=cid,
            truck_no=truck,
            from_loc=fr,
            to_loc=to,
            num_trips=trips,
            rate_per_trip=rate,
            total=trips * rate,
            invoice_date=today,
            trip_date=today,
        )
        db.session.add(r)
    db.session.commit()
    return jsonify(success=True, message="Demo data seeded.")


# ---------------------------------------------------------------------------

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
