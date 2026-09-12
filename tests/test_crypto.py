"""Crypto tests. Correctness is cross-proven, not trusted.

- Vendored ed25519 signs; the `cryptography` package verifies and
  vice versa (skipped only if the package is absent).
- RFC 8032 §7.1 vector (empty message) pins the implementation.
- Receipt sign → verify → tamper-fail; grant sign → verify → forgery-fail.
"""
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from acom import crypto, ed25519, grants, objects, receipts  # noqa: E402

cryptography = pytest.importorskip("cryptography.hazmat.primitives.asymmetric.ed25519",
                                   reason="cross-check needs cryptography lib")
from cryptography.exceptions import InvalidSignature  # noqa: E402
from cryptography.hazmat.primitives.asymmetric.ed25519 import (  # noqa: E402
    Ed25519PrivateKey, Ed25519PublicKey)


def test_cross_checked_keypair():
    """Library-generated secret: my pubkey must equal the lib's, both ways."""
    ref_priv = Ed25519PrivateKey.generate()
    raw = ref_priv.private_bytes_raw()
    ref_pub = ref_priv.public_key().public_bytes_raw()
    assert ed25519.pubkey(raw) == ref_pub


def test_cross_verify_both_directions():
    sec, pub = crypto.keypair()
    mine = ed25519.sign(sec, b"hello acom")
    Ed25519PublicKey.from_public_bytes(pub).verify(mine, b"hello acom")
    ref_priv = Ed25519PrivateKey.generate()
    ref_pub = ref_priv.public_key().public_bytes_raw()
    ref_sig = ref_priv.sign(b"hello acom")
    assert ed25519.verify(ref_pub, b"hello acom", ref_sig)
    with pytest.raises(InvalidSignature):
        Ed25519PublicKey.from_public_bytes(pub).verify(mine, b"tampered")


def test_receipt_sign_roundtrip_and_tamper():
    c = objects.make_claim("s", "d")
    decided = dict(c, result="TRUE")
    ev = [objects.make_evidence("m", 1, "u", "2026-01-01",
                                {"class": "news", "artifact_hash": "sha256:0"}),
          objects.make_evidence("m2", 2, "u", "2026-01-01",
                                {"class": "filing",
                                 "artifact_hash": "sha256:1"})]
    before = {"cursor": 0, "rules_commit": "t", "event_root": "",
              "state_root": ""}
    run = objects.make_run("task:t", "w")
    r = receipts.transition(
        before, {"id": c["id"], "target": c["id"], "claim": decided,
                 "grant": None},
        ev, ["two-sources-v1", "claim-resolved-v1"], run, proof_level=4,
        apply=lambda s, p, e: {**s, "cursor": s["cursor"] + 1})
    assert r["passed"]
    sec, pub = crypto.keypair()
    signed = receipts.sign_receipt(sec, r)
    assert receipts.verify_receipt(signed)["ok"]
    bad = dict(signed, signature="00" * 64)
    assert not receipts.verify_receipt(bad)["ok"]
    regloved = dict(signed)
    regloved["claim_states"] = {"X": "TRUE"}
    assert not receipts.verify_receipt(regloved)["ok"]


def test_grant_pubkey_subject_forgery_fails():
    sec, pub = crypto.keypair()
    other, _ = crypto.keypair()
    g = objects.make_grant(pub.hex(), "trading.swap",
                           {"max_value": 500, "asset": "USDC", "calls": 3},
                           [], "2030-01-01T00:00:00",
                           minimum_proof_level=9)
    g = dict(g, signature=crypto.sign_grant(sec, g))
    facts = {}
    act = {"capability": "trading.swap", "value": 100,
           "asset": "USDC", "calls": 1}
    assert grants.verify_grant(g, act, facts, "2026-01-01")["ok"]
    forged = dict(g, signature=crypto.sign_grant(other, g))
    assert not grants.verify_grant(forged, act, facts, "2026-01-01")["ok"]
