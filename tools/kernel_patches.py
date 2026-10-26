#!/usr/bin/env python3
"""Add or remove the HdcpPatch entry in PeerPressure's kernel_patches.bin.

PeerPressure applies Hdd1:\\PeerPressure\\System\\kernel_patches.bin to the kernel at boot. The
file is a list of entries, each `u32 address, u32 byte count, <count bytes of code>`, big
endian, ending with 0xFFFFFFFF. HdcpPatch adds one entry: VdpIsHDCPEnabled = li r3,1 / blr.

    python3 tools/kernel_patches.py check  <kernel_patches.bin>
    python3 tools/kernel_patches.py add    <kernel_patches.bin>
    python3 tools/kernel_patches.py remove <kernel_patches.bin>

add/remove edit the file in place and keep the previous version as <file>.bak.
"""
import shutil
import struct
import sys

HDCP_ADDRESS = 0x800BBA70           # VdpIsHDCPEnabled, retail kernel 17559
HDCP_CODE = struct.pack(">II", 0x38600001, 0x4E800020)     # li r3, 1 / blr
TERMINATOR = 0xFFFFFFFF


class Error(Exception):
    pass


def parse(data):
    """Returns [(address, code bytes)]; raises Error unless the file is well formed."""
    entries, pos = [], 0
    while True:
        if pos + 4 > len(data):
            raise Error("no 0xFFFFFFFF terminator - not a kernel_patches.bin file?")
        address = struct.unpack_from(">I", data, pos)[0]
        if address == TERMINATOR:
            if pos + 4 != len(data):
                raise Error("%d unexpected bytes after the terminator" % (len(data) - pos - 4))
            return entries
        if pos + 8 > len(data):
            raise Error("truncated entry at offset 0x%X" % pos)
        size = struct.unpack_from(">I", data, pos + 4)[0]
        if not 0x80000000 <= address < 0x80200000 or size == 0 or size % 4 or size > 0x1000:
            raise Error("implausible entry at offset 0x%X: address 0x%08X, %d bytes" % (pos, address, size))
        if pos + 8 + size > len(data):
            raise Error("truncated entry at offset 0x%X" % pos)
        entries.append((address, data[pos + 8:pos + 8 + size]))
        pos += 8 + size


def build(entries):
    out = bytearray()
    for address, code in entries:
        out += struct.pack(">II", address, len(code)) + code
    return bytes(out + struct.pack(">I", TERMINATOR))


def find_hdcp(entries):
    """Index of our entry, or None. Raises if another patch overlaps the HdcpPatch range."""
    for i, (address, code) in enumerate(entries):
        if address == HDCP_ADDRESS and code == HDCP_CODE:
            return i
        if address < HDCP_ADDRESS + len(HDCP_CODE) and HDCP_ADDRESS < address + len(code):
            raise Error("existing patch at 0x%08X (%d bytes) overlaps VdpIsHDCPEnabled - not touching it"
                        % (address, len(code)))
    return None


def main(argv):
    if len(argv) != 3 or argv[1] not in ("check", "add", "remove"):
        sys.exit(__doc__)
    command, path = argv[1], argv[2]
    with open(path, "rb") as f:
        data = f.read()
    entries = parse(data)
    index = find_hdcp(entries)
    print("%s: %d patches, HdcpPatch %s" % (path, len(entries), "present" if index is not None else "not present"))

    if command == "check":
        return
    if command == "add":
        if index is not None:
            print("nothing to do")
            return
        entries.append((HDCP_ADDRESS, HDCP_CODE))
    else:
        if index is None:
            print("nothing to do")
            return
        del entries[index]

    out = build(entries)
    assert parse(out) == entries
    shutil.copyfile(path, path + ".bak")
    with open(path, "wb") as f:
        f.write(out)
    print("%s HdcpPatch (%d -> %d bytes); previous file saved as %s.bak"
          % ("added" if command == "add" else "removed", len(data), len(out), path))


if __name__ == "__main__":
    try:
        main(sys.argv)
    except (Error, OSError) as e:
        sys.exit("error: %s" % e)
