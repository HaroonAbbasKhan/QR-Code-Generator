# QR Code Generator

A simple desktop app (Python + Tkinter) that generates QR codes from
different kinds of input: plain text, URLs, phone numbers, emails, SMS,
and WiFi credentials.

## Features

- Dropdown to pick what kind of data you're encoding
- Form fields change automatically based on the type you pick
- Live preview of the generated QR code
- Custom foreground/background colors
- Save the result as a PNG
- Input validation with clear error messages

Supported types:

| Type          | What it generates                                   |
|---------------|------------------------------------------------------|
| Plain Text    | Encodes the raw text                                  |
| URL / Website | A clickable link (adds `https://` if missing)         |
| Phone Number  | A `tel:` link that opens the dialer when scanned       |
| Email         | A `mailto:` link with optional subject/body            |
| SMS           | An `SMSTO:` payload that opens a pre-filled text message |
| WiFi Network  | A `WIFI:` payload that lets phones auto-join the network |

## Setup

1. Make sure you have Python 3.8+ installed.
2. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

   > Note: Tkinter usually ships with Python. On some Linux distros you may
   > need to install it separately, e.g. `sudo apt install python3-tk`.

## Run

```bash
python main.py
```

1. Pick a type from the dropdown (e.g. "URL / Website").
2. Fill in the fields that appear.
3. (Optional) Click the color buttons to customize the QR code's colors.
4. Click **Generate QR Code**.
5. Click **Save as PNG** to save it to your computer.

## Project structure

```
qr_code_generator/
├── main.py            # App: GUI + QR generation logic
├── requirements.txt   # Python dependencies
└── README.md
```

## Notes

- The payload-building logic (`build_payload` and the `build_*_payload`
  functions in `main.py`) is separated from the GUI code, so it can be
  reused or unit-tested independently of Tkinter.
- QR codes use medium error correction and auto-sized version fitting
  (`qrcode.constants.ERROR_CORRECT_M`, `fit=True`).
