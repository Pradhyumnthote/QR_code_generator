from django.shortcuts import render
from django.http import HttpResponse
from cryptography.fernet import Fernet
import base64
import hashlib
import qrcode
import random
from django.utils.http import urlencode
import os

def home(request):
    return render(request, '') 

# Derive a 32-byte Fernet key from a 6-character OTP
def derive_fernet_key(otp):
    sha256_hash = hashlib.sha256(otp.encode()).digest()
    fernet_key = base64.urlsafe_b64encode(sha256_hash[:32])
    return fernet_key

# Generate a numeric OTP (6 digits)
def generate_otp():
    return f"{random.randint(100000, 999999)}"

# Encrypt data using OTP
def encrypt_data(data, otp_key):
    fernet_key = derive_fernet_key(otp_key)
    f = Fernet(fernet_key)
    return f.encrypt(data.encode()).decode()

# Decrypt data using OTP
def decrypt_data(encrypted_data, otp_key):
    fernet_key = derive_fernet_key(otp_key)
    f = Fernet(fernet_key)
    return f.decrypt(encrypted_data.encode()).decode()  # Ensure encoding/decoding is consistent


# Generate QR code with a decryption link
# decryptor/views.py

def create_encrypted_qr(data, otp_key, host_url, output_file):
    encrypted_data = encrypt_data(data, otp_key)  # Encrypt the data
    link = f"{host_url}/decrypt/?data={encrypted_data}"  # Create a link with encrypted data
    
    # Create a QR code with the decryption link
    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(link)
    qr.make(fit=True)
    
    # Generate and save the QR code image
    img = qr.make_image(fill="black", back_color="white")
    img.save(output_file)  # Save the image to the specified file path
    
    return encrypted_data, output_file  # Return the encrypted data and the image file path



def decrypt_page(request):
    encrypted_data = request.GET.get('data', '')  # Retrieve the encrypted data from the URL
    decrypted_data = None
    error = None

    if request.method == 'POST':
        otp = request.POST.get('otp', '')  # Retrieve OTP from the form
        if not otp:
            error = "OTP is required."
        else:
            try:
                decrypted_data = decrypt_data(encrypted_data, otp)  # Decrypt using OTP
            except Exception as e:
                error = "Invalid OTP or corrupted data."

    return render(request, 'decrypt_page.html', {
        'decrypted_data': decrypted_data,
        'error': error,
    })


# Home page for generating QR codes
# decryptor/views.py
from django.conf import settings

# Home page for generating QR codes
def home(request):
    if request.method == 'POST':
        # Get student details from the form
        student_name = request.POST.get('name')
        student_class = request.POST.get('class')
        roll_no = request.POST.get('roll_no')

        # Combine details into a single string
        student_data = f"Name: {student_name}, Class: {student_class}, Roll No: {roll_no}"

        # Generate OTP and QR code
        host_url = request.build_absolute_uri('/')[:-1]  # Get the host URL
        otp_key = generate_otp()
        
        # Generate the QR code and save the image file
        encrypted_data, qr_file = create_encrypted_qr(student_data, otp_key, host_url, "encrypted_qr_with_link.png")

        # Save the QR code image to the file system in MEDIA_ROOT
        qr_path = os.path.join(settings.MEDIA_ROOT, qr_file)
        
        # Create the directory if it doesn't exist
        os.makedirs(settings.MEDIA_ROOT, exist_ok=True)
        
        # Save the image file to the specified location
        qr_file_path = os.path.join(settings.MEDIA_ROOT, qr_file)
        with open(qr_file_path, 'wb') as f:
            with open(qr_file, 'rb') as qr_image:
                f.write(qr_image.read())

        # Provide a link to download the QR code image
        download_url = f"{request.build_absolute_uri('/')[:-1]}/media/{qr_file}"
        
        return HttpResponse(
            f"<h1>QR Code Generated</h1>"
            f"<p>OTP: {otp_key}</p>"
            f"<p>Download the QR code:</p>"
            f"<a href='{download_url}'>Click here to download the QR code</a>"
        )

    return render(request, 'home.html')
