"""System test: calculate.py end-to-end seeing monitor (Seeing_monitor.pdf).

Requires production CLI (not yet implemented — expected RED until tddimplementer):

    python calculate.py -constants <file> -data <directory>
"""

from __future__ import annotations

import math
import os
import subprocess
import sys
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
FIXTURES = REPO_ROOT / "tests" / "fixtures"
CONSTANTS_PATH = FIXTURES / "constants" / "mock_telescope.constants"
DATA_DIR = FIXTURES / "data" / "mock_polaris_sequence"
CALCULATE_PY = REPO_ROOT / "calculate.py"

# Residual amplitudes baked into tests/fixtures/build_mock_data.py
AMP_X = 0.5
AMP_Y = 0.4
EXPECTED_SIGMA_STAR_SQ_PIXEL = AMP_X**2 + AMP_Y**2


def _parse_constants(path: Path) -> dict[str, float]:
    values: dict[str, float] = {}
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, val = line.split("=", 1)
        values[key.strip()] = float(val.strip())
    return values


def _parse_kv_stdout(text: str) -> dict[str, float]:
    values: dict[str, float] = {}
    for raw in text.splitlines():
        line = raw.strip()
        if not line or "=" not in line:
            continue
        key, val = line.split("=", 1)
        key = key.strip()
        try:
            values[key] = float(val.strip())
        except ValueError:
            continue
    return values


def expected_outputs(constants: dict[str, float]) -> dict[str, float]:
    """Analytic results from Seeing_monitor.pdf given mock residual amplitudes."""
    dm = constants["LENS_DIAMETER_M"]
    fm = constants["FOCAL_LENGTH_M"]
    pix = constants["PIXEL_SIZE_M"]
    lam = constants["WAVELENGTH_M"]
    k = constants["K"]
    z_deg = constants["ZENITH_DISTANCE_DEG"]

    scale = 206265.0 * pix / fm
    scale_rad = pix / fm
    sigma_pix = EXPECTED_SIGMA_STAR_SQ_PIXEL
    sigma_rad = sigma_pix * (scale_rad**2)

    # Eq. (5): r0 = (K λ² / σ_*^2)^0.6 * (1/Dm)^0.2
    r0_p = ((k * lam**2) / sigma_rad) ** 0.6 * (1.0 / dm) ** 0.2
    # Eq. (6): FWHM(arcsec) = 0.98 * λ / r0 * 206265
    fwhm_p = 0.98 * lam / r0_p * 206265.0

    cos_z = math.cos(math.radians(z_deg))
    # Eqs. (2) and (7) in the PDF
    fwhm_z = fwhm_p / (cos_z ** -0.6)
    r0_z = r0_p * (cos_z ** -0.6)

    return {
        "SCALE_ARCSEC_PER_PIXEL": scale,
        "SIGMA_STAR_SQ_PIXEL": sigma_pix,
        "SIGMA_STAR_SQ_RAD": sigma_rad,
        "R0_M": r0_p,
        "FWHM_ARCSEC": fwhm_p,
        "R0_ZENITH_M": r0_z,
        "FWHM_ZENITH_ARCSEC": fwhm_z,
    }


class CalculateSeeingMonitorSystemTest(unittest.TestCase):
    """Full workflow: mock constants + mock FITS data → PDF seeing products."""

    @classmethod
    def setUpClass(cls) -> None:
        cube = DATA_DIR / "polaris_cube.fits"
        if not cube.is_file():
            builder = FIXTURES / "build_mock_data.py"
            subprocess.run([sys.executable, str(builder)], check=True, cwd=str(REPO_ROOT))
        cls.assertTrue(cube.is_file(), f"missing fixture cube: {cube}")

    def test_fixtures_match_pdf_example_scale(self) -> None:
        constants = _parse_constants(CONSTANTS_PATH)
        scale = (
            206265.0
            * constants["PIXEL_SIZE_M"]
            / constants["FOCAL_LENGTH_M"]
        )
        # PDF Fig. 1/2 example uses Scale = 5.5 arcsec/pixel, Dm = 0.05 m
        self.assertAlmostEqual(scale, 5.5, places=3)
        self.assertAlmostEqual(constants["LENS_DIAMETER_M"], 0.05, places=12)
        self.assertAlmostEqual(constants["WAVELENGTH_M"], 5.5e-7, places=20)
        self.assertAlmostEqual(constants["K"], 0.358, places=12)

    def test_calculate_cli_prints_zenith_corrected_seeing(self) -> None:
        self.assertTrue(
            CALCULATE_PY.is_file(),
            "calculate.py missing — hand off to tddimplementer (red TDD expected)",
        )

        env = os.environ.copy()
        env["PYTHONPATH"] = str(REPO_ROOT) + os.pathsep + env.get("PYTHONPATH", "")

        proc = subprocess.run(
            [
                sys.executable,
                str(CALCULATE_PY),
                "-constants",
                str(CONSTANTS_PATH),
                "-data",
                str(DATA_DIR),
            ],
            cwd=str(REPO_ROOT),
            capture_output=True,
            text=True,
            env=env,
            check=False,
        )

        self.assertEqual(
            proc.returncode,
            0,
            msg=(
                "calculate.py failed\n"
                f"stdout:\n{proc.stdout}\n"
                f"stderr:\n{proc.stderr}"
            ),
        )

        got = _parse_kv_stdout(proc.stdout)
        expected = expected_outputs(_parse_constants(CONSTANTS_PATH))

        required = [
            "SCALE_ARCSEC_PER_PIXEL",
            "SIGMA_STAR_SQ_PIXEL",
            "SIGMA_STAR_SQ_RAD",
            "R0_M",
            "FWHM_ARCSEC",
            "R0_ZENITH_M",
            "FWHM_ZENITH_ARCSEC",
        ]
        for key in required:
            self.assertIn(key, got, f"missing stdout key {key}; stdout:\n{proc.stdout}")

        # Scale and injected residual variance should be essentially exact
        self.assertAlmostEqual(got["SCALE_ARCSEC_PER_PIXEL"], expected["SCALE_ARCSEC_PER_PIXEL"], places=6)
        self.assertAlmostEqual(got["SIGMA_STAR_SQ_PIXEL"], expected["SIGMA_STAR_SQ_PIXEL"], places=2)

        # Centroiding + poly fit introduce tiny error; keep relative tolerance modest
        for key in (
            "SIGMA_STAR_SQ_RAD",
            "R0_M",
            "FWHM_ARCSEC",
            "R0_ZENITH_M",
            "FWHM_ZENITH_ARCSEC",
        ):
            self.assertAlmostEqual(
                got[key],
                expected[key],
                delta=max(abs(expected[key]) * 0.05, 1e-12),
                msg=f"{key}: got={got[key]} expected={expected[key]}",
            )


if __name__ == "__main__":
    unittest.main()
