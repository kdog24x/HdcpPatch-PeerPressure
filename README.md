# HdcpPatch for PeerPressure

Fixes **"Secure HDCP link not found"** when playing DVDs over HDMI on an Xbox 360 running the
[PeerPressure](https://github.com/grimdoomer/Xbox360PeerPressure) softmod.

This is a port of [**HdcpPatch** by 5C8](https://github.com/5C8/HdcpPatch). The patch itself, the
kernel address and the two instructions, is theirs. The original is a DashLaunch plugin, and
PeerPressure can't load DashLaunch plugins, so this project applies the same patch a different
way: it adds it to PeerPressure's own `kernel_patches.bin`, which PeerPressure applies to the
kernel at every boot.

- **Works on:** retail kernel 17559 with PeerPressure (tested on v1.0.477).
- **Status:** confirmed working on one console. Reports from other consoles and PeerPressure
  versions are welcome.

> [!NOTE]
> **AI notice.** This project was written with the help of an AI assistant (Claude, by
> Anthropic): the reverse engineering of PeerPressure's patch loader, the script and this README.
> A person tested it on real hardware. Read the script before you run it; it's short.

> [!WARNING]
> This edits a file PeerPressure loads into the kernel at boot. It's been tested, but you use it
> at your own risk. Keep the backup the script makes.

HDCP is a copy-protection scheme. Like the original, this is meant for watching discs you own, not
for capturing protected content, which may be illegal where you live.

## Requirements

- FTP access to the console (for example, Aurora's FTP server)
- Python 3 on a PC (no extra packages)

## Install

1. Over FTP, download `Hdd1:\PeerPressure\System\kernel_patches.bin`.
2. Add the HdcpPatch entry:

   ```bash
   python3 tools/kernel_patches.py add kernel_patches.bin
   ```

   It should print `added HdcpPatch (372 -> 388 bytes)` (sizes may differ on other PeerPressure
   versions). Your untouched original is saved as `kernel_patches.bin.bak`.
3. Upload the edited `kernel_patches.bin` (not the `.bak`) back to `Hdd1:\PeerPressure\System\`,
   replacing the original.
4. Fully power the console off and on, then play a DVD over HDMI.

To check the file on the console, download it again and run:

```bash
python3 tools/kernel_patches.py check kernel_patches.bin
```

It prints `HdcpPatch present` or `HdcpPatch not present`.

## Uninstall

Either upload your `kernel_patches.bin.bak`, renamed to `kernel_patches.bin`, or run this on a
fresh download and upload the result:

```bash
python3 tools/kernel_patches.py remove kernel_patches.bin
```

Then power the console off and on.

## Notes

- **PeerPressure updates replace `kernel_patches.bin`.** After updating, repeat the install steps.
- The script refuses to edit a file it doesn't recognise, or one where another patch already
  covers the HdcpPatch address. Removing the entry gives back the original file byte for byte.
- If the console ever fails to boot in hacked mode after this change, boot it in retail mode and
  re-run the PeerPressure installer to restore its stock system files.
- Muted DVD audio, or the console reporting DVI instead of HDMI, is an EDID problem, not HDCP.
  See "Issue 2" in the [original HdcpPatch README](https://github.com/5C8/HdcpPatch#readme).
- PeerPressure's author doesn't support modified installs, so remove this before filing a
  PeerPressure bug report.

## How it works

`kernel_patches.bin` is a list of big-endian entries, each `u32 address, u32 byte count, <code>`,
ending with `0xFFFFFFFF`. At boot, PeerPressure copies each entry's code to its address in the
kernel.

`tools/kernel_patches.py` appends one entry, the same patch the original HdcpPatch makes:

| Address | Function | New code |
|---|---|---|
| `0x800BBA70` | `VdpIsHDCPEnabled` (retail 17559) | `li r3, 1` / `blr` (always return TRUE) |

None of PeerPressure's own patches touch that address.

## Credits

- [**HdcpPatch**](https://github.com/5C8/HdcpPatch) by 5C8: the original project and the patch
  this applies. It is in turn based on
  [UsbdSecPatch](https://github.com/InvoxiPlayGames/UsbdSecPatch) by InvoxiPlayGames.
- [**PeerPressure**](https://github.com/grimdoomer/Xbox360PeerPressure) by Grimdoomer: the softmod
  and its kernel patch loader.
- [hiddriver360-PeerPressure](https://github.com/RenaeTheRaven/hiddriver360-PeerPressure): its
  notes on PeerPressure's internals helped with the reverse engineering.

No files from PeerPressure or the original HdcpPatch are included in this repository.

## License

[MIT](LICENSE). This covers the script and documentation in this repository only.
