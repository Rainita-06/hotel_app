# app1/utils.py
import os
from django.conf import settings
import pywhatkit as kit

def send_whatsapp_voucher(phone_number, voucher):
    message = f"""
Grand Sunshine Hotel
Room: {voucher.room_no}
Guest: {voucher.customer_name}

Here is your Breakfast Voucher:
Adults: {voucher.adults}, Kids: {voucher.kids}
Date: {voucher.created_at.strftime('%d-%m-%Y')}

Please scan the QR below when entering the restaurant.

Thank you for choosing us!
"""

    # Send text instantly
    kit.sendwhatmsg_instantly(phone_number, message, wait_time=10, tab_close=True)

    # ✅ Send QR image file if exists
    if voucher.qr_code:  # e.g. /media/qrcodes/voucher_20.png
        qr_path = voucher.qr_code.replace("/media/", "")  
        qr_full_path = os.path.join(settings.MEDIA_ROOT, qr_path)

        if os.path.exists(qr_full_path):
            kit.sendwhats_image(
                phone_number,
                qr_full_path,
                caption=f"Breakfast Voucher (Room {voucher.room_no}, Guest {voucher.customer_name})"
            )
