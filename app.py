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
    <link href="https://fonts.googleapis.com/css2?family=Poppins:wght@400;600&display=swap" rel="stylesheet">
    <style>
        body {{
            font-family: 'Poppins', sans-serif;
            font-size: 15px;
            color: #333;
            background-color: #f5f7fa;
            margin: 0;
            padding: 0;
        }}
        .invoice-box {{
            max-width: 900px;
            margin: 40px auto;
            padding: 30px;
            background: #fff;
            border-radius: 12px;
            box-shadow: 0 6px 18px rgba(0, 0, 0, 0.1);
        }}
        .invoice-header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 20px;
        }}
        .company-details h1 {{
            font-size: 26px;
            color: #000; /* Reverted to default black */
            margin: 0;
        }}
        .invoice-meta p {{
            margin: 4px 0;
            font-weight: 500;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin-top: 20px;
            border-radius: 8px;
            overflow: hidden;
        }}
        th {{
            background: #dfe7f5;        /* Softer blue */
            color: #002752;             /* Deep readable text */
            font-weight: 700;
            padding: 14px 12px;
            text-align: left;
            letter-spacing: 0.3px;
            font-size: 15px;
            border-bottom: 2px solid #c0cde0;
        }}
        td {{
            padding: 12px;
            border-bottom: 1px solid #e1e1e1;
        }}
        tfoot td {{
            font-weight: 600;
            background: #f8f8f8;
        }}
        .thankyou {{
            margin-top: 30px;
            font-size: 16px;
            font-style: italic;
            text-align: center;
            color: #555;
        }}
        .print-btn {{
            text-align: center;
            margin-top: 30px;
        }}
        button {{
            background-color: #007BFF;
            color: white;
            padding: 12px 24px;
            border: none;
            border-radius: 6px;
            cursor: pointer;
            font-size: 15px;
            box-shadow: 0 2px 6px rgba(0, 123, 255, 0.4);
            transition: background 0.3s;
        }}
        button:hover {{
            background-color: #0056b3;
        }}

        @media (max-width: 768px) {{
            .invoice-header {{
                flex-direction: column;
                align-items: flex-start;
                gap: 10px;
            }}
            th, td {{
                font-size: 14px;
            }}
        }}

        @media print {{
            button, .print-btn {{
                display: none;
            }}
            body {{
                background: none;
            }}
            .invoice-box {{
                box-shadow: none;
                border: none;
            }}
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

        <p class="thankyou">Thank you for your business!</p>

        <div class="print-btn">
            <button onclick="window.print()">Print / Save as PDF</button>
        </div>
    </div>
    """

    return jsonify({'invoiceHtml': invoice_html})

if __name__ == '__main__':
    shivshakti_invoice_app.run(debug=False, host="0.0.0.0", port=5000)
