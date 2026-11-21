"""``autoswkit`` CLI — flag-compatible port of the case reference decryptor
(work/autosw/decrypt_tool.py)."""

from __future__ import annotations

import argparse
import json
import sys

from autoswkit.crypto import auto_decrypt, decrypt_request, decrypt_response, encrypt_request, encrypt_response


def _pretty(text: str) -> str:
    try:
        return json.dumps(json.loads(text), indent=2, ensure_ascii=False)
    except Exception:
        return text


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="autoswkit",
        description="Summoners War packet decryptor/encryptor (AutoSW revival toolkit)",
    )
    parser.add_argument("-r", "--request", help="Decrypt a request payload string")
    parser.add_argument("-p", "--response", help="Decrypt a response payload string")
    parser.add_argument("-a", "--auto", help="Auto-detect and decrypt a payload string")
    parser.add_argument("-f", "--file", help="Read encrypted payload from file")
    parser.add_argument("-e", "--encrypt", action="store_true", help="Encrypt --text instead of decrypting")
    parser.add_argument("--response-mode", action="store_true", help="With -e: build a response envelope (zlib)")
    parser.add_argument("--text", help="Plaintext to encrypt (with -e)")
    parser.add_argument("-v", "--version", type=int, default=2, choices=[1, 2], help="Key version (default 2)")
    parser.add_argument("-k", "--key", default="", help="Custom 16-byte key")
    parser.add_argument("-o", "--output", help="Save result to file")
    args = parser.parse_args(argv)

    if args.encrypt:
        if args.text is None:
            parser.error("-e/--encrypt requires --text")
        encrypt = encrypt_response if args.response_mode else encrypt_request
        result = encrypt(args.text, version=args.version, custom_key=args.key)
        print(result)
        if args.output:
            with open(args.output, "w", encoding="utf-8") as f:
                f.write(result)
        return 0

    payload = None
    mode = None
    if args.request:
        payload, mode = args.request, "request"
    elif args.response:
        payload, mode = args.response, "response"
    elif args.auto:
        payload, mode = args.auto, "auto"
    elif args.file:
        try:
            with open(args.file, "r", encoding="utf-8", errors="ignore") as f:
                payload = f.read().strip()
        except OSError as exc:
            print(f"[-] Cannot read {args.file}: {exc}", file=sys.stderr)
            return 1
        mode = "auto"
    else:
        print("No input given. Paste encrypted base64 payload and press Enter:")
        try:
            payload = input("> ").strip()
        except (KeyboardInterrupt, EOFError):
            return 0
        mode = "auto"

    if not payload:
        print("[-] Empty payload.", file=sys.stderr)
        return 1

    try:
        if mode == "request":
            result, kind = decrypt_request(payload, args.version, args.key), f"request (v{args.version})"
        elif mode == "response":
            result, kind = decrypt_response(payload, args.version, args.key), f"response (v{args.version})"
        else:
            kind, result = auto_decrypt(payload, args.version, args.key)
    except Exception as exc:
        print(f"[-] Decryption error: {exc}", file=sys.stderr)
        return 1

    formatted = _pretty(result)
    print(f"\n[+] Decrypted successfully (Type: {kind}):\n")
    print(formatted)
    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(formatted)
        print(f"\n[+] Saved to: {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
