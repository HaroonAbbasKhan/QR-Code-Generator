import qrcode

def generate_qr(data, filename="my_qr.png"):
    # 1. Configure the QR code's appearance and complexity
    qr = qrcode.QRCode(
        version=1, # Controls size (1 is smallest, up to 40)
        error_correction=qrcode.constants.ERROR_CORRECT_H, # High error correction
        box_size=10, # Size of each 'pixel' in the QR code
        border=4, # Thickness of the white border (4 is minimum standard)
    )

    # 2. Feed your data into the QR code
    qr.add_data(data)
    qr.make(fit=True)

    # 3. Generate the actual image (you can change colors here)
    img = qr.make_image(fill_color="black", back_color="white")

    # 4. Save the file
    img.save(filename)
    print(f"Success! QR code saved as {filename}")


# --- Try it out with different types of data ---

# Example 1: A standard website URL
generate_qr("https://www.python.org", "website_qr.png")

# Example 2: A phone number (using the standard 'tel:' prefix)
generate_qr("tel:+1234567890", "phone_qr.png")

# Example 3: A pre-filled SMS message
generate_qr("smsto:+1234567890:Hello, this is a test message!", "sms_qr.png")