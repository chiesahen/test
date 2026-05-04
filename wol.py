#!/usr/bin/env python3
"""
Wake-on-LAN packet sender
Usage: python wol.py <MAC> [IP] [port] [--subnet MASK] [--count N] [--interval S]
"""

import argparse
import socket
import struct
import sys
import time


def build_magic_packet(mac: str) -> bytes:
    mac_clean = mac.replace(":", "").replace("-", "").replace(".", "")
    if len(mac_clean) != 12:
        raise ValueError(f"Invalid MAC address: {mac}")
    try:
        mac_bytes = bytes.fromhex(mac_clean)
    except ValueError:
        raise ValueError(f"Invalid MAC address: {mac}")
    return b"\xff" * 6 + mac_bytes * 16


def send_magic_packet(
    mac: str,
    ip: str = "255.255.255.255",
    port: int = 9,
    subnet: str = None,
) -> None:
    packet = build_magic_packet(mac)
    target_ip = ip

    if subnet:
        # Compute broadcast address from IP + subnet mask
        ip_int = struct.unpack("!I", socket.inet_aton(ip))[0]
        mask_int = struct.unpack("!I", socket.inet_aton(subnet))[0]
        broadcast_int = ip_int | (~mask_int & 0xFFFFFFFF)
        target_ip = socket.inet_ntoa(struct.pack("!I", broadcast_int))

    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        sock.connect_ex((target_ip, port))
        sock.send(packet)

    print(f"Magic packet sent → MAC: {mac}  target: {target_ip}:{port}")


def main():
    parser = argparse.ArgumentParser(
        description="Send Wake-on-LAN magic packets (wolcmd-compatible)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
examples:
  python wol.py AA:BB:CC:DD:EE:FF
  python wol.py AA:BB:CC:DD:EE:FF 192.168.1.255
  python wol.py AA:BB:CC:DD:EE:FF 192.168.1.5 --subnet 255.255.255.0
  python wol.py AA:BB:CC:DD:EE:FF 192.168.1.255 9 --count 3 --interval 1
        """,
    )
    parser.add_argument("mac", help="Target MAC address (AA:BB:CC:DD:EE:FF or AA-BB-CC-DD-EE-FF)")
    parser.add_argument("ip", nargs="?", default="255.255.255.255", help="Target IP or broadcast address (default: 255.255.255.255)")
    parser.add_argument("port", nargs="?", type=int, default=9, help="UDP port (default: 9)")
    parser.add_argument("--subnet", metavar="MASK", help="Subnet mask to compute broadcast address (e.g. 255.255.255.0)")
    parser.add_argument("--count", type=int, default=1, metavar="N", help="Number of packets to send (default: 1)")
    parser.add_argument("--interval", type=float, default=1.0, metavar="S", help="Seconds between packets when --count > 1 (default: 1)")

    args = parser.parse_args()

    try:
        for i in range(args.count):
            if i > 0:
                time.sleep(args.interval)
            send_magic_packet(
                mac=args.mac,
                ip=args.ip,
                port=args.port,
                subnet=args.subnet,
            )
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    except PermissionError:
        print("Error: permission denied — try running with sudo", file=sys.stderr)
        sys.exit(1)
    except OSError as e:
        print(f"Network error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
