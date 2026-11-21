import struct
import hashlib
import os

orig_path = r"C:\Users\Andoru\.gemini\antigravity\brain\9efbcc20-2989-4e75-a627-d5db2c1e87f1\scratch\installed\caster.exe"
dest_path = r"C:\GitHub\reverse-skill\_investigate\RadioCaster 3.7.4.0 Multilingual\Crack Fixed\caster.exe"

with open(orig_path, "rb") as f:
    raw = bytearray(f.read())

print(f"Original binary size: {len(raw)} bytes")

# 1. Startup Registration Flag: RVA 0xd02992 -> File offset 0xd01d92
off_reg = 0xd01d92
assert raw[off_reg] == 0x01
raw[off_reg] = 0x00
print(f"[PATCH 1] Startup Registration: 0x{off_reg:x} -> 00 (Full Registered)")

# 2. Kill Demo Timer Watchdog (tmrDemoTimer): VA 0x140dbca60 -> RVA 0xdbca60 -> File offset 0xdbbe60
off_tmr_demo = 0xdbbe60
assert raw[off_tmr_demo : off_tmr_demo + 4] == b"\x48\x83\xec\x28"
raw[off_tmr_demo] = 0xc3 # ret
print(f"[PATCH 2] Kill tmrDemoTimer: 0x{off_tmr_demo:x} -> C3 (RET)")

# 3. Kill Demo Evaluation Core: VA 0x140db8e90 -> RVA 0xdb8e90 -> File offset 0xdb8290
off_demo_core = 0xdb8290
assert raw[off_demo_core] == 0x55 # push rbp
raw[off_demo_core] = 0xc3 # ret
print(f"[PATCH 3] Kill Demo Evaluation Core: 0x{off_demo_core:x} -> C3 (RET)")

# 4. Kill Online Update & Telemetry Checker (tmrUpdateChecker): VA 0x140dbcd60 -> RVA 0xdbcd60 -> File offset 0xdbc160
off_update = 0xdbc160
assert raw[off_update : off_update + 2] == b"\x55\x53" # push rbp; push rbx
raw[off_update] = 0xc3 # ret
print(f"[PATCH 4] Kill Update/Telemetry Timer: 0x{off_update:x} -> C3 (RET)")

# 5. Neutralize Audio Tone Stream Generator: VA 0x140c94430 -> RVA 0xc94430 -> File offset 0xc93830
off_tone = 0xc93830
assert raw[off_tone : off_tone + 3] == b"\x55\x56\x53" # push rbp; push rsi; push rbx
raw[off_tone : off_tone + 3] = b"\x31\xc0\xc3" # xor eax, eax; ret
print(f"[PATCH 5] Neutralize Audio Tone Generator: 0x{off_tone:x} -> XOR EAX, EAX; RET")

# 6. Disable radiocaster_guard.exe Spawning: VA 0x140db6a30 -> RVA 0xdb6a30 -> File offset 0xdb5e30
off_guard = 0xdb5e30
assert raw[off_guard : off_guard + 3] == b"\x55\x53\x48" # push rbp; push rbx; sub rsp...
raw[off_guard] = 0xc3 # ret
print(f"[PATCH 6] Disable radiocaster_guard.exe Spawning: 0x{off_guard:x} -> C3 (RET)")

# 7. BYPASS THE 1-5 MINUTE BROADCAST STREAMING DEMO BEEP INJECTION LOOP:
# VA 0x140db186e (Offset 0xdb0c6e): jne 0x140db19b1 -> jmp 0x140db19b1; nop
off_stream_loop = 0xdb0c6e
assert raw[off_stream_loop : off_stream_loop + 6] == b"\x0f\x85\x3d\x01\x00\x00"
raw[off_stream_loop : off_stream_loop + 6] = b"\xe9\x3e\x01\x00\x00\x90"
print(f"[PATCH 7a] Bypass Stream Demo Beep Loop Check: 0x{off_stream_loop:x} -> JMP 0x140db19b1")

# Failsafe jump inside loop at 0x140db1874 (Offset 0xdb0c74) -> jmp 0x140db19b1
off_loop_body = 0xdb0c74
assert raw[off_loop_body : off_loop_body + 5] == b"\xb9\xe0\x93\x04\x00"
raw[off_loop_body : off_loop_body + 5] = b"\xe9\x38\x01\x00\x00"
print(f"[PATCH 7b] Failsafe Kill Stream Demo Beep Loop Body: 0x{off_loop_body:x} -> JMP 0x140db19b1")

# 8. Disable broadcast overlay injection: VA 0x140763620 -> File offset 0x762a20
off_overlay = 0x762a20
assert raw[off_overlay : off_overlay + 3] == b"\x55\x41\x55" # push rbp; push r13...
raw[off_overlay] = 0xc3 # ret
print(f"[PATCH 8] Disable Broadcast Audio Overlay: 0x{off_overlay:x} -> C3 (RET)")

# 9. Airgap Patch: Neutralize remote DJSoft network endpoints inside binary
url_update = "https://www.djsoft.net/script/checkupdate3.php".encode('utf-16le')
dummy_update = "http://127.0.0.1/null.php\x00".encode('utf-16le')
pos = raw.find(url_update)
if pos != -1:
    raw[pos : pos + len(dummy_update)] = dummy_update
    print(f"[PATCH 9a] Airgap checkupdate URL: 0x{pos:x} -> 127.0.0.1")

url_bug = b"https://www.djsoft.net/bugreport"
dummy_bug = b"http://127.0.0.1/null\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
pos = raw.find(url_bug)
if pos != -1:
    raw[pos : pos + len(url_bug)] = dummy_bug[:len(url_bug)]
    print(f"[PATCH 9b] Airgap bugreport URL: 0x{pos:x} -> 127.0.0.1")

url_cloud = "https://www.djsoft.net/cloudsrv".encode('utf-16le')
dummy_cloud = "http://127.0.0.1/null\x00".encode('utf-16le')
pos = raw.find(url_cloud)
if pos != -1:
    raw[pos : pos + len(dummy_cloud)] = dummy_cloud
    print(f"[PATCH 9c] Airgap cloudsrv URL: 0x{pos:x} -> 127.0.0.1")

# Write to output destination
os.makedirs(os.path.dirname(dest_path), exist_ok=True)
with open(dest_path, "wb") as f:
    f.write(raw)

sha256 = hashlib.sha256(raw).hexdigest()
print(f"\nSuccessfully wrote comprehensive fixed binary to: {dest_path}")
print(f"File Size: {len(raw)} bytes")
print(f"SHA256: {sha256}")
