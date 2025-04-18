from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import requests
import os

def initiate_khalti_payment(request):
    """Initiate a payment request to Khalti."""
    if request.method == 'POST':
        url = "https://khalti.com/api/v2/payment/initiate/"
        headers = {
            "Authorization": f"Key 63f32942f293495e81d9126a9bc6085d",
            "Content-Type": "application/json"
        }
        data = {
            "return_url": "https://yourdomain.com/payment/callback/",
            "website_url": "https://yourdomain.com/",
            "amount": request.POST.get("amount"),
            "purchase_order_id": request.POST.get("purchase_order_id"),
            "purchase_order_name": request.POST.get("purchase_order_name"),
            "customer_info": {
                "name": request.POST.get("name"),
                "email": request.POST.get("email"),
                "phone": request.POST.get("phone")
            }
        }
        response = requests.post(url, headers=headers, json=data)
        return JsonResponse(response.json())
    
    return JsonResponse({"message": "Invalid request method."}, status=405)

def khalti_lookup_api(transaction_id):
    """Call Khalti Lookup API to verify transaction."""
    url = "https://khalti.com/api/v2/payment/lookup/"
    headers = {
        "Authorization": f"Key {os.getenv('KHALTI_SECRET_KEY')}"
    }
    data = {"transaction_id": transaction_id}
    response = requests.post(url, headers=headers, data=data)
    return response.json()

@csrf_exempt
def payment_success_callback(request):
    """Handle the payment success callback from Khalti."""
    if request.method == 'GET':
        pidx = request.GET.get('pidx')
        status = request.GET.get('status')
        transaction_id = request.GET.get('transaction_id')
        amount = request.GET.get('amount')
        mobile = request.GET.get('mobile')
        purchase_order_id = request.GET.get('purchase_order_id')
        purchase_order_name = request.GET.get('purchase_order_name')
        total_amount = request.GET.get('total_amount')
        
        if status == "Completed":
            # Call lookup API for confirmation
            lookup_response = khalti_lookup_api(transaction_id)
            if lookup_response.get("status") == "Completed":
                # Payment confirmed, process order or update database
                return JsonResponse({"message": "Payment confirmed", "data": lookup_response}, status=200)
            else:
                return JsonResponse({"message": "Payment lookup failed", "data": lookup_response}, status=400)
        
        elif status == "Pending":
            return JsonResponse({"message": "Payment is still pending. Please verify later."}, status=202)
        
        elif status == "User canceled":
            return JsonResponse({"message": "Payment was canceled by the user."}, status=400)
        
        else:
            return JsonResponse({"message": "Unknown status received."}, status=400)
    
    return JsonResponse({"message": "Invalid request method."}, status=405)
