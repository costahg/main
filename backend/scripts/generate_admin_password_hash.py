from __future__ import annotations

import getpass
import sys
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from security import generate_admin_password_hash  # noqa: E402


def main() -> int:
    password = getpass.getpass("Admin password: ")
    confirmation = getpass.getpass("Confirm admin password: ")

    if password != confirmation:
        print("Passwords do not match.", file=sys.stderr)
        return 1

    if not password:
        print("Password cannot be empty.", file=sys.stderr)
        return 1

    print(generate_admin_password_hash(password))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
