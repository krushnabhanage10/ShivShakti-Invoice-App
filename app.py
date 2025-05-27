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
        <link href="https://fonts.googleapis.com/css2?family=Roboto:wght@400;700&family=Open+Sans&display=swap" rel="stylesheet">
        <style>
            body {{
                font-family: 'Roboto', 'Open Sans', sans-serif;
                font-size: 14px;
                color: #333;
            }}
            .invoice-box {{
                max-width: 900px;
                margin: auto;
                padding: 30px;
                border: 1px solid #eee;
                box-shadow: 0 0 10px rgba(0, 0, 0, 0.15);
            }}
            .invoice-header {{
                display: flex;
                justify-content: space-between;
                align-items: center;
            }}
            .company-details h1 {{
                font-size: 24px;
                margin: 0;
            }}
            .invoice-meta p {{
                margin: 4px 0;
            }}
            table {{
                width: 100%;
                border-collapse: collapse;
                margin-top: 20px;
            }}
            th {{
                background: #f4f4f4;
                font-weight: 700;
                padding: 10px;
                text-align: left;
            }}
            td {{
                padding: 10px;
                border-bottom: 1px solid #ddd;
            }}
            tfoot td {{
                font-weight: 700;
                background: #f9f9f9;
            }}
            .thankyou {{
                margin-top: 30px;
                font-size: 16px;
                font-style: italic;
                text-align: center;
                color: #444;
            }}
            .print-btn {{
                text-align: center;
                margin-top: 20px;
            }}
            button {{
                background-color: #007BFF;
                color: white;
                padding: 10px 20px;
                border: none;
                border-radius: 4px;
                cursor: pointer;
                font-size: 14px;
            }}
        </style>

        <div class="invoice-box">
            <div class="invoice-header">
                <div class="logo-col">
                    <img id="previewLogo" src="/static/logo.png" alt="Logo" style="max-height: 80px;" />
                </div>
                <div class="company-details">
                    <h1>Shivshakti Transport</h1>
                    <p>Moshi, Pune<br/>Proprietor: Bharat Bhange</p>
                </div>
                <div class="invoice-meta">
                    <p><strong>Invoice No:</strong> {invoice_number}</p>
                    <p><strong>Date:</strong> {invoice_date}</p>
                </div>
            </div>

            <hr />

            <div>
                <strong>Invoice To:</strong><br/>
                <span>{client_name}</span><br/>
                <span>{client_address}</span>
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
                    <tbody>
                        {trip_rows_html}
                    </tbody>
                    <tfoot>
                        <tr>
                            <td colspan="5" style="text-align: right;"><strong>Grand Total (₹)</strong></td>
                            <td>₹{grand_total:.2f}</td>
                        </tr>
                    </tfoot>
                </table>
            </div>

            <p class="thankyou">Thank you !!!</p>

            <div class="print-btn">
                <button onclick="window.print()">Print / Save as PDF</button>
            </div>
        </div>
    """

    return jsonify({'invoiceHtml': invoice_html})

if __name__ == '__main__':
    shivshakti_invoice_app.run(debug=False, host="0.0.0.0", port=5000)
