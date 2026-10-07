"""Windows DPAPI Chromium cookie extraction for LinkedIn."""

from __future__ import annotations

import base64
import json
import logging
import os
import shutil
import sqlite3
import sys
import tempfile
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

BROWSER_PATHS = {
    "Chrome": Path(os.environ.get("LOCALAPPDATA", ""))
    / "Google"
    / "Chrome"
    / "User Data",
    "Edge": Path(os.environ.get("LOCALAPPDATA", ""))
    / "Microsoft"
    / "Edge"
    / "User Data",
    "Brave": Path(os.environ.get("LOCALAPPDATA", ""))
    / "BraveSoftware"
    / "Brave-Browser"
    / "User Data",
    "CocCoc": Path(os.environ.get("LOCALAPPDATA", ""))
    / "CocCoc"
    / "Browser"
    / "User Data",
}


class CookieImporter:
    @staticmethod
    def get_supported_browsers() -> list[str]:
        return [b for b, p in BROWSER_PATHS.items() if p.exists()]

    @staticmethod
    def _decrypt_key_dpapi(encrypted_key: bytes) -> bytes | None:
        if sys.platform != "win32":
            return None
        import ctypes
        from ctypes import wintypes

        class DATA_BLOB(ctypes.Structure):
            _fields_ = [
                ("cbData", wintypes.DWORD),
                ("pbData", ctypes.POINTER(ctypes.c_char)),
            ]

        blob_in = DATA_BLOB(
            len(encrypted_key),
            ctypes.create_string_buffer(encrypted_key, len(encrypted_key)),
        )
        blob_out = DATA_BLOB()

        crypt32 = ctypes.windll.crypt32
        CryptUnprotectData = crypt32.CryptUnprotectData
        CryptUnprotectData.argtypes = [
            ctypes.POINTER(DATA_BLOB),
            ctypes.POINTER(wintypes.LPWSTR),
            ctypes.POINTER(DATA_BLOB),
            ctypes.c_void_p,
            ctypes.c_void_p,
            wintypes.DWORD,
            ctypes.POINTER(DATA_BLOB),
        ]
        CryptUnprotectData.restype = wintypes.BOOL

        if CryptUnprotectData(
            ctypes.byref(blob_in), None, None, None, None, 0, ctypes.byref(blob_out)
        ):
            key = ctypes.string_at(blob_out.pbData, blob_out.cbData)
            ctypes.windll.kernel32.LocalFree(blob_out.pbData)
            return key
        return None

    @classmethod
    def import_linkedin_cookies(cls, browser_name: str = "Chrome") -> dict[str, Any]:
        """Import and decrypt LinkedIn cookies on Windows."""
        if sys.platform != "win32":
            return {
                "status": "UNSUPPORTED_OS",
                "error": "Cookie DPAPI decryption only available on Windows.",
            }

        user_data = BROWSER_PATHS.get(browser_name)
        if not user_data or not user_data.exists():
            return {
                "status": "NOT_FOUND",
                "error": f"Browser user data directory for {browser_name} not found.",
            }

        local_state_file = user_data / "Local State"
        if not local_state_file.exists():
            return {
                "status": "NOT_FOUND",
                "error": f"Local State file missing in {browser_name}.",
            }

        # Cookie file candidates
        cookie_candidates = [
            user_data / "Default" / "Network" / "Cookies",
            user_data / "Default" / "Cookies",
            user_data / "Profile 1" / "Network" / "Cookies",
        ]
        cookie_file = next((c for c in cookie_candidates if c.exists()), None)
        if not cookie_file:
            return {
                "status": "NOT_FOUND",
                "error": f"Cookies database not found for {browser_name}.",
            }

        try:
            local_state = json.loads(local_state_file.read_text(encoding="utf-8"))
            encrypted_key_b64 = local_state.get("os_crypt", {}).get("encrypted_key")
            if not encrypted_key_b64:
                return {
                    "status": "FAIL",
                    "error": "os_crypt encrypted_key not present in Local State.",
                }

            encrypted_key = base64.b64decode(encrypted_key_b64)
            if encrypted_key.startswith(b"DPAPI"):
                encrypted_key = encrypted_key[5:]

            aes_key = cls._decrypt_key_dpapi(encrypted_key)
            if not aes_key:
                return {
                    "status": "UNSUPPORTED_ENCRYPTION",
                    "error": "Failed to decrypt master key via DPAPI. App-bound encryption (Chromium 127+) requires persistent browser profile login.",
                }

            # Copy DB to temp to avoid lock
            with tempfile.NamedTemporaryFile(delete=False) as tmp_db:
                tmp_path = Path(tmp_db.name)
            shutil.copyfile(cookie_file, tmp_path)

            cookies = []
            conn = sqlite3.connect(tmp_path)
            cursor = conn.cursor()
            cursor.execute(
                "SELECT host_key, name, path, encrypted_value, is_secure, expires_utc "
                "FROM cookies WHERE host_key LIKE '%linkedin.com%'"
            )
            rows = cursor.fetchall()
            conn.close()
            try:
                tmp_path.unlink()
            except Exception:
                pass

            from cryptography.hazmat.primitives.ciphers.aead import AESGCM

            for host_key, name, path, enc_val, is_secure, expires_utc in rows:
                if not enc_val:
                    continue
                decrypted_val = None
                try:
                    if enc_val.startswith(b"v10") or enc_val.startswith(b"v11"):
                        nonce = enc_val[3:15]
                        ciphertext = enc_val[15:]
                        aesgcm = AESGCM(aes_key)
                        decrypted_val = aesgcm.decrypt(nonce, ciphertext, None).decode(
                            "utf-8"
                        )
                    elif enc_val.startswith(b"v20"):
                        # Chrome 127+ App-bound encryption
                        return {
                            "status": "UNSUPPORTED_APP_BOUND_ENCRYPTION",
                            "error": "Modern Chromium App-Bound Encryption detected (v20). Automatic DPAPI decryption is blocked by OS. Use dedicated persistent browser profile to log in once: 'linkedin-agent session login'.",
                        }
                    else:
                        raw = cls._decrypt_key_dpapi(enc_val)
                        if raw:
                            decrypted_val = raw.decode("utf-8", errors="ignore")
                except Exception as e:
                    logger.debug(f"Failed to decrypt cookie {name}: {e}")

                if decrypted_val:
                    cookies.append(
                        {
                            "name": name,
                            "value": decrypted_val,
                            "domain": host_key,
                            "path": path,
                            "secure": bool(is_secure),
                        }
                    )

            li_at = next((c for c in cookies if c["name"] == "li_at"), None)
            if not li_at:
                return {
                    "status": "NO_SESSION_COOKIE",
                    "error": "LinkedIn li_at cookie not found in browser database. Log in via browser first.",
                }

            return {
                "status": "SUCCESS",
                "cookie_count": len(cookies),
                "has_li_at": True,
                "cookies": cookies,
            }
        except Exception as e:
            return {"status": "FAIL", "error": f"Error importing cookies: {e!s}"}
