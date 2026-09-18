#!/usr/bin/env python3
"""
Lab: Hashing & MAC  --  Part 5
Salting and key-derivation-function work factors.

No third-party packages (uses hashlib.pbkdf2_hmac and hashlib.scrypt). Run:
    python3 password_kdf_bench.py --passphrase "adalovelace-800123456!56"

Shows:
  1. SHA256(pw) with no salt          -> identical for every user with this pw
  2. SHA256(salt || pw), two salts    -> two different stored values, same pw
  3. PBKDF2-HMAC-SHA256 timing at 10k / 100k / 600k iterations
  4. scrypt timing
  5. estimated single-GPU offline guessing rate for each setting
"""

import argparse
import hashlib
import os
import time

# Rough order-of-magnitude raw SHA-256 throughput for one modern high-end GPU.
# Used only to turn "seconds per hash" into "guesses per second" for Q15.
GPU_RAW_SHA256_PER_SEC = 20_000_000_000        # ~20 GH/s


def sha256_hex(data):
    return hashlib.sha256(data).hexdigest()


def timed(fn, *args, reps=3):
    best = float("inf")
    for _ in range(reps):
        t0 = time.perf_counter()
        fn(*args)
        best = min(best, time.perf_counter() - t0)
    return best


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--passphrase", default="student-000000000!00",
                    help="your PASS (SIP) value")
    args = ap.parse_args()
    pw = args.passphrase.encode()

    print(f"[*] passphrase (PASS): {args.passphrase}\n")

    # ---- 1 & 2: salting -------------------------------------------------
    print("--- unsalted vs salted SHA-256 ---------------------------------")
    print(f"SHA256(pw)                 = {sha256_hex(pw)}")
    salt_a = os.urandom(16)
    salt_b = os.urandom(16)
    print(f"salt A                    = {salt_a.hex()}")
    print(f"SHA256(saltA || pw)       = {sha256_hex(salt_a + pw)}")
    print(f"salt B                    = {salt_b.hex()}")
    print(f"SHA256(saltB || pw)       = {sha256_hex(salt_b + pw)}")
    print("  -> same password, two salts, two completely different stored digests\n")

    # ---- 3 & 4: work-factor timing ------------------------------------
    print("--- KDF work factor (time for ONE verification) ---------------")
    salt = os.urandom(16)
    header = f"{'algorithm':<28}{'time / hash':>14}{'est. GPU guesses/sec':>24}"
    print(header)
    print("-" * len(header))

    raw_t = timed(hashlib.sha256, salt + pw, reps=50)
    print(f"{'raw SHA-256':<28}{raw_t * 1e6:>11.1f} us"
          f"{GPU_RAW_SHA256_PER_SEC:>24,}")

    for iters in (10_000, 100_000, 600_000):
        t = timed(hashlib.pbkdf2_hmac, "sha256", pw, salt, iters)
        # PBKDF2-HMAC-SHA256 ~= 2 * iters SHA-256 compressions
        rate = int(GPU_RAW_SHA256_PER_SEC / (2 * iters))
        print(f"{'PBKDF2-HMAC-SHA256 x' + f'{iters:,}':<28}"
              f"{t * 1e3:>11.2f} ms{rate:>24,}")

    # scrypt: N=2**15 (32768), r=8, p=1  -> ~32 MiB working memory
    n, r, p = 2 ** 15, 8, 1
    try:
        t = timed(lambda: hashlib.scrypt(pw, salt=salt, n=n, r=r, p=p,
                                         maxmem=128 * 1024 * 1024))
        mem_mib = 128 * n * r / (1024 * 1024)
        print(f"{'scrypt N=2^15,r=8,p=1':<28}{t * 1e3:>11.2f} ms"
              f"   memory-hard (~{mem_mib:.0f} MiB per guess)")
    except ValueError as e:
        print(f"scrypt skipped: {e}")

    print()
    print("For Q13: read your own numbers off the table above -- the 'time / hash'")
    print("and 'est. GPU guesses/sec' columns are what the question asks you to")
    print("compare. Your measured times will differ from anyone else's machine.")


if __name__ == "__main__":
    main()
