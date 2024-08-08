import os
import requests
import uuid
  
def create_paypal_invoice(amount, language="English"):
  headers = {
      'Authorization': 'Bearer zekwhYgsYYI0zDg0p_Nf5v78VelCfYR0',
      'Content-Type': 'application/json',
      'Prefer': 'return=representation',
  }

  # generate random uuid
  invoice_id = uuid.uuid4()

  payload = {
    "detail": {
      "currency_code": "USD"
    },
    "items": [
      {
        "name": "Yoga Mat",
        "description": "Elastic mat to practice yoga.",
        "quantity": "1",
        "unit_amount": {
          "currency_code": "USD",
          "value": "10.00"
        },
      },
    ]
  }


  response = requests.post('https://api-m.sandbox.paypal.com/v2/invoicing/invoices', headers=headers, json=payload)
  url = response['detail']['metadata']['recipient_view_url']
  print(url)

