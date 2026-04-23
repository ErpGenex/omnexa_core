from __future__ import annotations

import re
import sys
from dataclasses import dataclass
from pathlib import Path

try:
	import tkinter as tk
	from tkinter import filedialog, messagebox, ttk
except Exception as e:  # pragma: no cover
	tk = None  # type: ignore[assignment]
	_fatal_tk_error = e

from generator import generate_license_jwt, generate_offline_activation_key


_APP_RE = re.compile(r"^omnexa_[a-z0-9_]+$")


@dataclass(frozen=True)
class FormValues:
	private_key_path: str
	app_slug: str
	aud: str
	months: int
	customer_id: str
	kid: str
	issuer: str
	support_email: str
	padding_bytes: int


def _read_private_key_pem(path_s: str) -> str:
	p = Path(path_s)
	if not p.exists():
		raise ValueError("Private key file not found.")
	text = p.read_text(encoding="utf-8").strip()
	if "BEGIN" not in text or "PRIVATE KEY" not in text:
		raise ValueError("Selected file doesn't look like a PEM private key.")
	return text


def _copy_to_clipboard(root, text: str) -> None:
	root.clipboard_clear()
	root.clipboard_append(text)
	root.update()


if tk is not None:

	class App(tk.Tk):  # type: ignore[misc]
		def __init__(self) -> None:
			super().__init__()
			self.title("ErpGenEx License Key Generator (Windows)")
			self.geometry("860x640")
			self.minsize(820, 600)

			self._build_ui()

		def _build_ui(self) -> None:
			outer = ttk.Frame(self, padding=12)
			outer.pack(fill=tk.BOTH, expand=True)

			frm = ttk.Labelframe(outer, text="Inputs", padding=12)
			frm.pack(fill=tk.X)

			self.var_private_key = tk.StringVar(value="")
			self.var_app = tk.StringVar(value="omnexa_tourism")
			self.var_aud = tk.StringVar(value="erpgenex.local.site")
			self.var_months = tk.IntVar(value=12)
			self.var_customer = tk.StringVar(value="cust-1001")
			self.var_kid = tk.StringVar(value="shop-2026-1")
			self.var_issuer = tk.StringVar(value="https://erpgenex.com")
			self.var_support_email = tk.StringVar(value="info@erpgenex.com")
			self.var_padding = tk.IntVar(value=1024)

			row = 0

			ttk.Label(frm, text="Private key PEM").grid(row=row, column=0, sticky="w")
			ent_key = ttk.Entry(frm, textvariable=self.var_private_key, width=70)
			ent_key.grid(row=row, column=1, sticky="we", padx=(8, 8))
			ttk.Button(frm, text="Browse…", command=self._browse_key).grid(row=row, column=2, sticky="e")
			row += 1

			ttk.Label(frm, text="App slug (omnexa_*)").grid(row=row, column=0, sticky="w", pady=(8, 0))
			ttk.Entry(frm, textvariable=self.var_app).grid(row=row, column=1, sticky="we", padx=(8, 8), pady=(8, 0))
			row += 1

			ttk.Label(frm, text="Audience (aud)").grid(row=row, column=0, sticky="w", pady=(8, 0))
			ttk.Entry(frm, textvariable=self.var_aud).grid(row=row, column=1, sticky="we", padx=(8, 8), pady=(8, 0))
			ttk.Label(frm, text="(must match omnexa_license_expected_aud)").grid(row=row, column=2, sticky="w", pady=(8, 0))
			row += 1

			ttk.Label(frm, text="Plan months").grid(row=row, column=0, sticky="w", pady=(8, 0))
			months_box = ttk.Combobox(frm, width=10, state="readonly", values=[1, 3, 6, 12, 24, 36])
			months_box.set(str(self.var_months.get()))
			months_box.grid(row=row, column=1, sticky="w", padx=(8, 8), pady=(8, 0))
			months_box.bind("<<ComboboxSelected>>", lambda _e: self.var_months.set(int(months_box.get())))
			row += 1

			ttk.Label(frm, text="Customer ID (sub)").grid(row=row, column=0, sticky="w", pady=(8, 0))
			ttk.Entry(frm, textvariable=self.var_customer).grid(row=row, column=1, sticky="we", padx=(8, 8), pady=(8, 0))
			row += 1

			ttk.Label(frm, text="Key ID (kid) [optional]").grid(row=row, column=0, sticky="w", pady=(8, 0))
			ttk.Entry(frm, textvariable=self.var_kid).grid(row=row, column=1, sticky="we", padx=(8, 8), pady=(8, 0))
			row += 1

			ttk.Label(frm, text="Issuer (iss)").grid(row=row, column=0, sticky="w", pady=(8, 0))
			ttk.Entry(frm, textvariable=self.var_issuer).grid(row=row, column=1, sticky="we", padx=(8, 8), pady=(8, 0))
			row += 1

			ttk.Label(frm, text="Support email").grid(row=row, column=0, sticky="w", pady=(8, 0))
			ttk.Entry(frm, textvariable=self.var_support_email).grid(row=row, column=1, sticky="we", padx=(8, 8), pady=(8, 0))
			row += 1

			ttk.Label(frm, text="Offline padding bytes").grid(row=row, column=0, sticky="w", pady=(8, 0))
			ttk.Spinbox(frm, from_=0, to=16384, increment=64, textvariable=self.var_padding, width=12).grid(
				row=row, column=1, sticky="w", padx=(8, 8), pady=(8, 0)
			)
			row += 1

			frm.columnconfigure(1, weight=1)

			btns = ttk.Frame(outer, padding=(0, 12, 0, 0))
			btns.pack(fill=tk.X)
			ttk.Button(btns, text="Generate JWT", command=self._generate_jwt).pack(side=tk.LEFT)
			ttk.Button(btns, text="Generate Offline Key (ERPGX1-...)", command=self._generate_offline).pack(
				side=tk.LEFT, padx=(8, 0)
			)
			ttk.Button(btns, text="Generate Both", command=self._generate_both).pack(side=tk.LEFT, padx=(8, 0))

			out = ttk.Labelframe(outer, text="Output", padding=12)
			out.pack(fill=tk.BOTH, expand=True, pady=(12, 0))

			self.txt_out = tk.Text(out, wrap=tk.WORD, height=18)
			self.txt_out.pack(fill=tk.BOTH, expand=True)

			copy_row = ttk.Frame(outer, padding=(0, 10, 0, 0))
			copy_row.pack(fill=tk.X)
			ttk.Button(copy_row, text="Copy Output", command=self._copy_output).pack(side=tk.LEFT)
			ttk.Button(copy_row, text="Clear", command=self._clear_output).pack(side=tk.LEFT, padx=(8, 0))

			foot = ttk.Label(
				outer,
				text="Tip: For Marketplace tests, paste JWT or ERPGX1 key into the license field, and keep aud consistent with site_config.",
			)
			foot.pack(anchor="w", pady=(10, 0))

		def _browse_key(self) -> None:
			path = filedialog.askopenfilename(
				title="Select RSA private key (PEM)",
				filetypes=[("PEM files", "*.pem"), ("All files", "*.*")],
			)
			if path:
				self.var_private_key.set(path)

		def _get_values(self) -> FormValues:
			private_key_path = (self.var_private_key.get() or "").strip()
			app_slug = (self.var_app.get() or "").strip()
			aud = (self.var_aud.get() or "").strip()
			customer_id = (self.var_customer.get() or "").strip()
			kid = (self.var_kid.get() or "").strip()
			issuer = (self.var_issuer.get() or "").strip()
			support_email = (self.var_support_email.get() or "").strip()

			try:
				months = int(self.var_months.get())
			except Exception:
				months = 0
			try:
				padding_bytes = int(self.var_padding.get())
			except Exception:
				padding_bytes = -1

			if not private_key_path:
				raise ValueError("Please select a private key PEM file.")
			if not app_slug or not _APP_RE.match(app_slug):
				raise ValueError("Invalid app slug. Must look like omnexa_something.")
			if not aud:
				raise ValueError("Audience (aud) is required.")
			if not customer_id:
				raise ValueError("Customer ID is required.")
			if months not in (1, 3, 6, 12, 24, 36):
				raise ValueError("Plan months must be one of: 1, 3, 6, 12, 24, 36.")
			if padding_bytes < 0 or padding_bytes > 16384:
				raise ValueError("Padding bytes must be between 0 and 16384.")

			return FormValues(
				private_key_path=private_key_path,
				app_slug=app_slug,
				aud=aud,
				months=months,
				customer_id=customer_id,
				kid=kid,
				issuer=issuer or "https://erpgenex.com",
				support_email=support_email or "info@erpgenex.com",
				padding_bytes=padding_bytes,
			)

		def _set_output(self, text: str) -> None:
			self.txt_out.delete("1.0", tk.END)
			self.txt_out.insert(tk.END, text.strip() + "\n")

		def _append_output(self, text: str) -> None:
			if self.txt_out.get("1.0", tk.END).strip():
				self.txt_out.insert(tk.END, "\n")
			self.txt_out.insert(tk.END, text.strip() + "\n")
			self.txt_out.see(tk.END)

		def _generate_jwt(self) -> None:
			try:
				v = self._get_values()
				private_pem = _read_private_key_pem(v.private_key_path)
				token = generate_license_jwt(
					private_key_pem=private_pem,
					app_slug=v.app_slug,
					site_aud=v.aud,
					months=v.months,
					customer_id=v.customer_id,
					key_id=v.kid or None,
					issuer=v.issuer,
					support_email=v.support_email,
				)
				self._set_output(token)
			except Exception as e:
				messagebox.showerror("Error", str(e))

		def _generate_offline(self) -> None:
			try:
				v = self._get_values()
				private_pem = _read_private_key_pem(v.private_key_path)
				key = generate_offline_activation_key(
					private_key_pem=private_pem,
					app_slug=v.app_slug,
					site_aud=v.aud,
					months=v.months,
					customer_id=v.customer_id,
					key_id=v.kid or None,
					issuer=v.issuer,
					support_email=v.support_email,
					padding_bytes=v.padding_bytes,
				)
				self._set_output(key)
			except Exception as e:
				messagebox.showerror("Error", str(e))

		def _generate_both(self) -> None:
			try:
				v = self._get_values()
				private_pem = _read_private_key_pem(v.private_key_path)
				token = generate_license_jwt(
					private_key_pem=private_pem,
					app_slug=v.app_slug,
					site_aud=v.aud,
					months=v.months,
					customer_id=v.customer_id,
					key_id=v.kid or None,
					issuer=v.issuer,
					support_email=v.support_email,
				)
				key = generate_offline_activation_key(
					private_key_pem=private_pem,
					app_slug=v.app_slug,
					site_aud=v.aud,
					months=v.months,
					customer_id=v.customer_id,
					key_id=v.kid or None,
					issuer=v.issuer,
					support_email=v.support_email,
					padding_bytes=v.padding_bytes,
				)
				self._set_output(token)
				self._append_output("----")
				self._append_output(key)
			except Exception as e:
				messagebox.showerror("Error", str(e))

		def _copy_output(self) -> None:
			text = self.txt_out.get("1.0", tk.END).strip()
			if not text:
				return
			_copy_to_clipboard(self, text)
			messagebox.showinfo("Copied", "Output copied to clipboard.")

		def _clear_output(self) -> None:
			self.txt_out.delete("1.0", tk.END)


def main() -> None:
	if tk is None:
		raise SystemExit(
			"tkinter is not available in this Python environment.\n"
			"On Windows, install Python from python.org (includes tkinter), then run:\n"
			"  python gui.py\n"
			f"Details: {_fatal_tk_error}"
		)
	app = App()
	app.mainloop()


if __name__ == "__main__":
	main()

