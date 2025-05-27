// static/script.js
let tripIndex = 0;

function addTripRow() {
  const tripRows = document.getElementById("tripRows");
  const row = document.createElement("div");
  row.classList.add("trip-row");
  row.innerHTML = `
    <input type="text" placeholder="Truck No" id="truckNo-${tripIndex}">
    <input type="text" placeholder="From" id="from-${tripIndex}">
    <input type="text" placeholder="To" id="to-${tripIndex}">
    <input type="number" placeholder="Trips" id="trips-${tripIndex}">
    <input type="number" placeholder="Rate/Trip" id="rate-${tripIndex}">
  `;
  tripRows.appendChild(row);
  tripIndex++;
}

async function generateInvoice() {
  const clientName = document.getElementById("clientName").value;
  const clientAddress = document.getElementById("clientAddress").value;

  const tripsData = [];
  for (let i = 0; i < tripIndex; i++) {
    const truck = document.getElementById(`truckNo-${i}`);
    const from = document.getElementById(`from-${i}`);
    const to = document.getElementById(`to-${i}`);
    const trips = document.getElementById(`trips-${i}`);
    const rate = document.getElementById(`rate-${i}`);

    if (truck && from && to && trips && rate) {
      tripsData.push({
        truckNo: truck.value,
        from: from.value,
        to: to.value,
        trips: parseInt(trips.value) || 0,
        rate: parseFloat(rate.value) || 0,
      });
    }
  }

  try {
    const response = await fetch('/generate_invoice', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        clientName: clientName,
        clientAddress: clientAddress,
        trips: tripsData,
      }),
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    const data = await response.json();
    document.getElementById("invoicePreview").innerHTML = data.invoiceHtml;
    document.getElementById("invoicePreview").classList.remove("hidden");

  } catch (error) {
    console.error('Error generating invoice:', error);
    // You might want to display an error message to the user here
  }
}