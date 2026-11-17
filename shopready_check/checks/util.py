# SPDX-License-Identifier: GPL-3.0-or-later
def mb(n):
    """Bytes as a short size string, in MiB when the number is a whole MiB."""
    if n >= 1048576 and n % 1048576 == 0:
        return f"{n // 1048576} MiB"
    if n >= 1_000_000:
        return f"{n / 1_000_000:.1f} MB"
    return f"{max(n, 0) / 1000:.0f} kB"


def cm(m):
    v = m * 100.0
    return f"{v:.1f}" if abs(v) < 100 else f"{v:.0f}"


def faces_payload(pairs):
    """[(mesh name, [face idx])] -> select payload, empty lists dropped."""
    faces = {name: idx for name, idx in pairs if idx}
    return {"faces": faces} if faces else {}
