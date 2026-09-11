"""
QR Code Generator
-----------------
A simple desktop app (Tkinter GUI) that lets a user pick a data type
(URL, Phone Number, Email, SMS, WiFi, Plain Text), fill in a small form,
and generate + preview + save a QR code image.

Run:
    python main.py

Requirements:
    pip install -r requirements.txt
"""

import re
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, colorchooser

import qrcode
from PIL import Image, ImageTk
#hedllo

# --------------------------------------------------------------------------
# Payload builders (pure functions -- no GUI dependency, easy to test)
# --------------------------------------------------------------------------

def build_text_payload(data):
    text = data.get("text", "").strip()
    if not text:
        raise ValueError("Please enter some text.")
    return text


def build_url_payload(data):
    url = data.get("url", "").strip()
    if not url:
        raise ValueError("Please enter a URL.")
    if not re.match(r"^[a-zA-Z][a-zA-Z0-9+.-]*://", url):
        url = "https://" + url
    return url


def build_phone_payload(data):
    phone = data.get("phone", "").strip()
    if not phone:
        raise ValueError("Please enter a phone number.")
    cleaned = re.sub(r"[^\d+]", "", phone)
    if not re.match(r"^\+?\d{6,15}$", cleaned):
        raise ValueError("Phone number looks invalid. Use digits, optionally starting with +.")
    return f"tel:{cleaned}"


def build_email_payload(data):
    email = data.get("email", "").strip()
    subject = data.get("subject", "").strip()
    body = data.get("body", "").strip()
    if not email:
        raise ValueError("Please enter an email address.")
    if not re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", email):
        raise ValueError("Email address looks invalid.")
    payload = f"mailto:{email}"
    params = []
    if subject:
        params.append("subject=" + subject.replace(" ", "%20"))
    if body:
        params.append("body=" + body.replace(" ", "%20").replace("\n", "%0A"))
    if params:
        payload += "?" + "&".join(params)
    return payload


def build_sms_payload(data):
    phone = data.get("phone", "").strip()
    message = data.get("message", "").strip()
    if not phone:
        raise ValueError("Please enter a phone number.")
    cleaned = re.sub(r"[^\d+]", "", phone)
    if not re.match(r"^\+?\d{6,15}$", cleaned):
        raise ValueError("Phone number looks invalid. Use digits, optionally starting with +.")
    return f"SMSTO:{cleaned}:{message}"


def build_wifi_payload(data):
    ssid = data.get("ssid", "").strip()
    password = data.get("password", "")
    encryption = data.get("encryption", "WPA")
    hidden = data.get("hidden", False)
    if not ssid:
        raise ValueError("Please enter a network name (SSID).")
    if encryption != "nopass" and not password:
        raise ValueError("Please enter a WiFi password, or set encryption to None.")

    def esc(s):
        return re.sub(r'([\\;,:"])', r"\\\1", s)

    enc = "" if encryption == "nopass" else encryption
    return f"WIFI:T:{enc};S:{esc(ssid)};P:{esc(password)};H:{'true' if hidden else 'false'};;"


PAYLOAD_BUILDERS = {
    "Plain Text": build_text_payload,
    "URL / Website": build_url_payload,
    "Phone Number": build_phone_payload,
    "Email": build_email_payload,
    "SMS": build_sms_payload,
    "WiFi Network": build_wifi_payload,
}


def build_payload(qr_type, data):
    builder = PAYLOAD_BUILDERS.get(qr_type)
    if builder is None:
        raise ValueError(f"Unknown QR type: {qr_type}")
    return builder(data)


# --------------------------------------------------------------------------
# GUI
# --------------------------------------------------------------------------

BG = "#f5f5f7"
CARD_BG = "#ffffff"
ACCENT = "#2f6fed"
TEXT = "#1c1c1e"
MUTED = "#6b6b70"


class QRCodeGeneratorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("QR Code Generator")
        self.root.geometry("460x700")
        self.root.minsize(420, 640)
        self.root.configure(bg=BG)

        self.qr_type_var = tk.StringVar(value="URL / Website")
        self.fill_color = "#000000"
        self.back_color = "#ffffff"
        self.qr_image = None      # full-resolution PIL image
        self.qr_photo = None      # Tk-displayable preview image
        self.field_vars = {}      # currently active field widgets/vars

        self._build_layout()
        self._render_fields_for_type()

    # ---------------- layout ----------------

    def _build_layout(self):
        header = tk.Frame(self.root, bg=BG)
        header.pack(fill="x", padx=20, pady=(20, 10))
        tk.Label(header, text="QR Code Generator", font=("Helvetica", 20, "bold"),
                  bg=BG, fg=TEXT).pack(anchor="w")
        tk.Label(header, text="Pick a type, fill in the details, generate.",
                  font=("Helvetica", 11), bg=BG, fg=MUTED).pack(anchor="w")

        # Type selector
        type_frame = tk.Frame(self.root, bg=BG)
        type_frame.pack(fill="x", padx=20, pady=(5, 10))
        tk.Label(type_frame, text="Type", font=("Helvetica", 11, "bold"),
                  bg=BG, fg=TEXT).pack(anchor="w")
        self.type_combo = ttk.Combobox(
            type_frame, textvariable=self.qr_type_var,
            values=list(PAYLOAD_BUILDERS.keys()), state="readonly", font=("Helvetica", 11)
        )
        self.type_combo.pack(fill="x", pady=(4, 0))
        self.type_combo.bind("<<ComboboxSelected>>", lambda e: self._render_fields_for_type())

        # Dynamic fields card
        self.fields_card = tk.Frame(self.root, bg=CARD_BG, highlightbackground="#e2e2e5",
                                     highlightthickness=1)
        self.fields_card.pack(fill="x", padx=20, pady=(0, 10))
        self.fields_inner = tk.Frame(self.fields_card, bg=CARD_BG)
        self.fields_inner.pack(fill="x", padx=14, pady=14)

        # Color options
        color_frame = tk.Frame(self.root, bg=BG)
        color_frame.pack(fill="x", padx=20, pady=(0, 10))
        self.fill_btn = tk.Button(color_frame, text="Foreground Color", command=self._pick_fill_color,
                                   bg="#000000", fg="white", relief="flat", padx=8, pady=6)
        self.fill_btn.pack(side="left", expand=True, fill="x", padx=(0, 5))
        self.back_btn = tk.Button(color_frame, text="Background Color", command=self._pick_back_color,
                                   bg="#ffffff", fg="black", relief="flat", padx=8, pady=6,
                                   highlightbackground="#cccccc")
        self.back_btn.pack(side="left", expand=True, fill="x", padx=(5, 0))

        # Action buttons
        action_frame = tk.Frame(self.root, bg=BG)
        action_frame.pack(fill="x", padx=20, pady=(0, 10))
        tk.Button(action_frame, text="Generate QR Code", command=self.generate_qr,
                  bg=ACCENT, fg="white", font=("Helvetica", 11, "bold"),
                  relief="flat", padx=10, pady=10).pack(side="left", expand=True, fill="x", padx=(0, 5))
        tk.Button(action_frame, text="Clear", command=self.clear_all,
                  bg="#e2e2e5", fg=TEXT, font=("Helvetica", 11),
                  relief="flat", padx=10, pady=10).pack(side="left", padx=(5, 0))

        # Preview
        preview_card = tk.Frame(self.root, bg=CARD_BG, highlightbackground="#e2e2e5",
                                 highlightthickness=1)
        preview_card.pack(fill="both", expand=True, padx=20, pady=(0, 10))
        self.preview_label = tk.Label(preview_card, text="QR code preview will appear here",
                                       bg=CARD_BG, fg=MUTED, font=("Helvetica", 10))
        self.preview_label.pack(expand=True, pady=20)

        self.save_btn = tk.Button(self.root, text="Save as PNG", command=self.save_qr,
                                   bg="#e2e2e5", fg=TEXT, font=("Helvetica", 11),
                                   relief="flat", padx=10, pady=8, state="disabled")
        self.save_btn.pack(fill="x", padx=20, pady=(0, 6))

        self.status_var = tk.StringVar(value="Ready.")
        tk.Label(self.root, textvariable=self.status_var, bg=BG, fg=MUTED,
                  font=("Helvetica", 9)).pack(fill="x", padx=20, pady=(0, 12))

    # ---------------- dynamic fields ----------------

    def _clear_fields(self):
        for widget in self.fields_inner.winfo_children():
            widget.destroy()
        self.field_vars = {}

    def _add_entry(self, label, key, show=None):
        tk.Label(self.fields_inner, text=label, bg=CARD_BG, fg=TEXT,
                  font=("Helvetica", 10)).pack(anchor="w", pady=(6, 2))
        var = tk.StringVar()
        entry = tk.Entry(self.fields_inner, textvariable=var, font=("Helvetica", 11),
                          relief="solid", bd=1, show=show)
        entry.pack(fill="x", ipady=4)
        self.field_vars[key] = var

    def _add_text(self, label, key, height=3):
        tk.Label(self.fields_inner, text=label, bg=CARD_BG, fg=TEXT,
                  font=("Helvetica", 10)).pack(anchor="w", pady=(6, 2))
        text = tk.Text(self.fields_inner, height=height, font=("Helvetica", 11),
                        relief="solid", bd=1)
        text.pack(fill="x")
        self.field_vars[key] = text  # Text widget: read via .get("1.0", "end")

    def _render_fields_for_type(self):
        self._clear_fields()
        qr_type = self.qr_type_var.get()

        if qr_type == "Plain Text":
            self._add_text("Text", "text", height=5)

        elif qr_type == "URL / Website":
            self._add_entry("Website URL (e.g. example.com)", "url")

        elif qr_type == "Phone Number":
            self._add_entry("Phone Number (e.g. +923001234567)", "phone")

        elif qr_type == "Email":
            self._add_entry("Email Address", "email")
            self._add_entry("Subject (optional)", "subject")
            self._add_text("Body (optional)", "body", height=3)

        elif qr_type == "SMS":
            self._add_entry("Phone Number", "phone")
            self._add_text("Message", "message", height=3)

        elif qr_type == "WiFi Network":
            self._add_entry("Network Name (SSID)", "ssid")
            self._add_entry("Password", "password", show="*")
            tk.Label(self.fields_inner, text="Encryption", bg=CARD_BG, fg=TEXT,
                      font=("Helvetica", 10)).pack(anchor="w", pady=(6, 2))
            enc_var = tk.StringVar(value="WPA")
            enc_combo = ttk.Combobox(self.fields_inner, textvariable=enc_var,
                                      values=["WPA", "WEP", "nopass"], state="readonly")
            enc_combo.pack(fill="x")
            self.field_vars["encryption"] = enc_var
            hidden_var = tk.BooleanVar(value=False)
            tk.Checkbutton(self.fields_inner, text="Hidden network", variable=hidden_var,
                            bg=CARD_BG, fg=TEXT).pack(anchor="w", pady=(6, 0))
            self.field_vars["hidden"] = hidden_var

    def _collect_field_values(self):
        data = {}
        for key, widget in self.field_vars.items():
            if isinstance(widget, tk.Text):
                data[key] = widget.get("1.0", "end").strip()
            elif isinstance(widget, tk.BooleanVar):
                data[key] = widget.get()
            else:
                data[key] = widget.get()
        return data

    # ---------------- colors ----------------

    def _pick_fill_color(self):
        color = colorchooser.askcolor(color=self.fill_color, title="Choose foreground color")
        if color[1]:
            self.fill_color = color[1]
            self.fill_btn.configure(bg=self.fill_color)

    def _pick_back_color(self):
        color = colorchooser.askcolor(color=self.back_color, title="Choose background color")
        if color[1]:
            self.back_color = color[1]
            self.back_btn.configure(bg=self.back_color)

    # ---------------- actions ----------------

    def generate_qr(self):
        data = self._collect_field_values()
        qr_type = self.qr_type_var.get()
        try:
            payload = build_payload(qr_type, data)
        except ValueError as e:
            messagebox.showerror("Invalid input", str(e))
            self.status_var.set(f"Error: {e}")
            return

        try:
            qr = qrcode.QRCode(
                version=None,
                error_correction=qrcode.constants.ERROR_CORRECT_M,
                box_size=10,
                border=4,
            )
            qr.add_data(payload)
            qr.make(fit=True)
            img = qr.make_image(fill_color=self.fill_color, back_color=self.back_color).convert("RGB")
        except Exception as e:
            messagebox.showerror("Generation failed", str(e))
            self.status_var.set(f"Error: {e}")
            return

        self.qr_image = img
        display_img = img.resize((280, 280))
        self.qr_photo = ImageTk.PhotoImage(display_img)
        self.preview_label.configure(image=self.qr_photo, text="")
        self.save_btn.configure(state="normal")
        self.status_var.set(f"QR code generated for {qr_type}.")

    def save_qr(self):
        if self.qr_image is None:
            return
        path = filedialog.asksaveasfilename(
            defaultextension=".png",
            filetypes=[("PNG image", "*.png"), ("All files", "*.*")],
            initialfile="qrcode.png",
        )
        if not path:
            return
        try:
            self.qr_image.save(path)
            self.status_var.set(f"Saved to {path}")
        except Exception as e:
            messagebox.showerror("Save failed", str(e))
            self.status_var.set(f"Error saving file: {e}")

    def clear_all(self):
        self._render_fields_for_type()
        self.qr_image = None
        self.qr_photo = None
        self.preview_label.configure(image="", text="QR code preview will appear here")
        self.save_btn.configure(state="disabled")
        self.status_var.set("Cleared.")


def main():
    root = tk.Tk()
    QRCodeGeneratorApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
