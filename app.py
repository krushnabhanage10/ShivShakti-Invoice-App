# app.py
import os
from flask import Flask, render_template, request, jsonify
import datetime

shivshakti_invoice_app = Flask(__name__)

STATIC_FOLDER = 'static'
if not os.path.exists(STATIC_FOLDER):
    os.makedirs(STATIC_FOLDER)

@shivshakti_invoice_app.route('/')
def index():
    return render_template('index.html')

@shivshakti_invoice_app.route('/generate_invoice', methods=['POST'])
def generate_invoice():
    data = request.json
    client_name = data.get('clientName', '')
    client_address = data.get('clientAddress', '')
    trips = data.get('trips', [])

    invoice_number = "INV-" + str(os.urandom(3).hex())
    invoice_date = datetime.date.today().strftime("%Y-%m-%d")

    trip_rows_html = ""
    grand_total = 0

    for trip in trips:
        truck_no = trip.get('truckNo', '')
        from_loc = trip.get('from', '')
        to_loc = trip.get('to', '')
        num_trips = int(trip.get('trips', 0))
        rate_per_trip = float(trip.get('rate', 0.0))

        total = num_trips * rate_per_trip
        grand_total += total

        trip_rows_html += f"""
            <tr>
                <td>{truck_no}</td>
                <td>{from_loc}</td>
                <td>{to_loc}</td>
                <td>{num_trips}</td>
                <td>₹{rate_per_trip:.2f}</td>
                <td>₹{total:.2f}</td>
            </tr>
        """

    invoice_html = f"""
        <div class="invoice-box">
            <div class="invoice-header">
                <div class="logo-col">
                    <img id="previewLogo" src="/static/logo.png" alt="Logo" class="logo" />
                </div>
                <div class="company-details">
                    <h1>Shivshakti Transport</h1>
                    <p>Moshi, Pune<br/>Proprietor: Bharat Bhange</p>
                </div>
                <div class="invoice-meta">
                    <p><strong>Invoice No:</strong> <span id="invoiceNumber">{invoice_number}</span></p>
                    <p><strong>Date:</strong> <span id="invoiceDate">{invoice_date}</span></p>
                </div>
            </div>

            <hr />

            <div>
                <strong>Invoice To:</strong><br/>
                <span id="outClientName">{client_name}</span><br/>
                <span id="outClientAddress">{client_address}</span>
            </div>

            <div class="trip-details">
                <table>
                    <thead>
                        <tr>
                            <th>Truck No</th>
                            <th>From</th>
                            <th>To</th>
                            <th>No. of Trips</th>
                            <th>Rate/Trip (₹)</th>
                            <th>Total (₹)</th>
                        </tr>
                    </thead>
                    <tbody id="tripTableBody">
                        {trip_rows_html}
                    </tbody>
                    <tfoot>
                        <tr>
                            <td colspan="5" style="text-align: right;"><strong>Grand Total (₹)</strong></td>
                            <td id="grandTotal">₹{grand_total:.2f}</td>
                        </tr>
                    </tfoot>
                </table>
            </div>

            <p class="thankyou">Thank you !!!</p>
        </div>

        <div class="print-btn">
            <button onclick="window.print()">Print / Save as PDF</button>
        </div>
    """
    return jsonify({'invoiceHtml': invoice_html})

if __name__ == '__main__':
    shivshakti_invoice_app.run(debug=True)