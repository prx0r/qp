"""Agent identities and signatures: the crypto that makes qp a primitive.

- Identity = Ed25519 pubkey (hex). Address = first 16 hex chars of
  sha256(pubkey): human-readable, collision-evident, never secret.
- Receipts are SIGNED over their id (see receipts.sign_receipt).
- Grants name pubkey subjects and verify cryptographically.
- Private keys live in the vault or the caller's memory. NEVER in the
  tree, NEVER in chat, NEVER in receipts. This module never persists.
"""
import os

from . import ed25519
from .canonical import sha256_hex


def keypair(secret: bytes = b"") -> tuple[bytes, bytes]:
    if not secret:
        secret = os.urandom(32)
    return secret, ed25519.pubkey(secret)


def address(pubkey: bytes) -> str:
    return sha256_hex(pubkey)[:16]


def sign_id(secret: bytes, receipt_id: str) -> str:
    return ed25519.sign(secret, receipt_id.encode()).hex()


def verify_id(pubkey_hex: str, receipt_id: str, signature_hex: str) -> bool:
    try:
        return ed25519.verify(bytes.fromhex(pubkey_hex),
                              receipt_id.encode(),
                              bytes.fromhex(signature_hex))
    except Exception:
        return False


def sign_grant(secret: bytes, grant: dict) -> str:
    from .canonical import canonical
    body = {k: v for k, v in grant.items()
            if k not in ("id", "signature")}
    return ed25519.sign(secret, canonical(body)).hex()


def verify_grant_sig(pubkey_hex: str, grant: dict, signature_hex: str) -> bool:
    from .canonical import canonical
    try:
        body = {k: v for k, v in grant.items()
                if k not in ("id", "signature")}
        return ed25519.verify(bytes.fromhex(pubkey_hex),
                              canonical(body),
                              bytes.fromhex(signature_hex))
    except Exception:
        return False
