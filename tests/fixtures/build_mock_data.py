#!/usr/bin/env python3
"""Regenerate synthetic Polaris FITS cube for system tests (test collateral only).

Builds a short cube whose stellar centers follow a known quadratic trend plus
known alternating residuals so analytic σ_*^2, r0, and FWHM are predictable.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np

# Must stay in sync with tests/system/test_calculate_seeing_monitor.py
N_FRAMES = 120
HEIGHT = 64
WIDTH = 64
GAUSS_SIGMA = 1.5
PEAK = 1000.0  # well below typical 16-bit saturation

# Quadratic drift (pixels) vs frame index t = 0 .. N-1
TREND_X = (32.0, 0.02, 1.5e-4)  # a0, a1, a2
TREND_Y = (30.0, -0.015, 1.0e-4)

# Alternating residuals → exact mean 0; σ_*^2 (pix) = AMP_X^2 + AMP_Y^2
AMP_X = 0.5
AMP_Y = 0.4


def residual_xy(t: int) -> tuple[float, float]:
    sx = AMP_X if (t % 2 == 0) else -AMP_X
    # period-4 pattern keeps mean Y exactly 0 over N_FRAMES divisible by 4
    sy = AMP_Y if (t % 4 in (0, 1)) else -AMP_Y
    return sx, sy


def true_center(t: int) -> tuple[float, float]:
    a0, a1, a2 = TREND_X
    b0, b1, b2 = TREND_Y
    dx, dy = residual_xy(t)
    x = a0 + a1 * t + a2 * t * t + dx
    y = b0 + b1 * t + b2 * t * t + dy
    return x, y


def expected_sigma_star_sq_pixel() -> float:
    return AMP_X**2 + AMP_Y**2


def gaussian_stamp(cy: float, cx: float) -> np.ndarray:
    yy, xx = np.indices((HEIGHT, WIDTH), dtype=np.float64)
    r2 = (xx - cx) ** 2 + (yy - cy) ** 2
    return PEAK * np.exp(-0.5 * r2 / (GAUSS_SIGMA**2))


def build_cube() -> np.ndarray:
    cube = np.empty((N_FRAMES, HEIGHT, WIDTH), dtype=np.float32)
    for t in range(N_FRAMES):
        # true_center returns (x, y) = (column, row) to match image convention
        x, y = true_center(t)
        cube[t] = gaussian_stamp(cy=y, cx=x).astype(np.float32)
    return cube


def _pad_card(card: str) -> bytes:
    raw = card.encode("ascii")
    if len(raw) > 80:
        raise ValueError(f"FITS card longer than 80: {card!r}")
    return raw + b" " * (80 - len(raw))


def write_fits_cube(path: Path, data: np.ndarray) -> None:
    """Minimal Primary-HDU FITS writer (float32, big-endian), no astropy required."""
    if data.ndim != 3:
        raise ValueError("expected (N, H, W) cube")
    naxis3, naxis2, naxis1 = data.shape
    header_cards = [
        "SIMPLE  =                    T / file does conform to FITS standard",
        "BITPIX  =                  -32 / IEEE single precision floating point",
        "NAXIS   =                    3 / number of data axes",
        f"NAXIS1  = {naxis1:20d} / length of data axis 1",
        f"NAXIS2  = {naxis2:20d} / length of data axis 2",
        f"NAXIS3  = {naxis3:20d} / length of data axis 3",
        "EXTEND  =                    T / FITS dataset may contain extensions",
        "OBJECT  = 'Polaris mock'       / synthetic system-test cube",
        "COMMENT Synthetic seeing-monitor sequence for automated tests",
        "END",
    ]
    header = b"".join(_pad_card(c) for c in header_cards)
    pad = (2880 - (len(header) % 2880)) % 2880
    header = header + (b" " * pad)

    # FITS multi-dimensional arrays are in Fortran order: NAXIS1 fastest
    payload = np.asarray(data, dtype=">f4").tobytes(order="C")
    # numpy C-order for (N,H,W) stores W fastest, then H, then N — matches
    # FITS NAXIS1=W, NAXIS2=H, NAXIS3=N when written as contiguous C floats.
    data_pad = (2880 - (len(payload) % 2880)) % 2880
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("wb") as fh:
        fh.write(header)
        fh.write(payload)
        if data_pad:
            fh.write(b"\x00" * data_pad)


def main() -> None:
    out_dir = Path(__file__).resolve().parent / "data" / "mock_polaris_sequence"
    out_path = out_dir / "polaris_cube.fits"
    cube = build_cube()
    write_fits_cube(out_path, cube)
    print(f"wrote {out_path} shape={cube.shape}")
    print(f"expected SIGMA_STAR_SQ_PIXEL={expected_sigma_star_sq_pixel()}")


if __name__ == "__main__":
    main()
