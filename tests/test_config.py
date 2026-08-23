"""Tests for first-milestone configuration contracts."""

from pathlib import Path
import unittest

from src.data.config import load_config


class ConfigTests(unittest.TestCase):
    def test_default_configuration_preserves_nb1_grid(self) -> None:
        config = load_config(Path("config/config.yaml"))
        self.assertEqual(
            config["grid"],
            {"size_meters": 3000, "geometry": "square", "metric_crs": "EPSG:2263"},
        )
        self.assertEqual(config["random_seed"], 42)
        self.assertEqual(config["time"]["interval_minutes"], 30)

    def test_invalid_grid_geometry_is_rejected(self) -> None:
        import tempfile

        with tempfile.TemporaryDirectory() as directory:
            config_file = Path(directory) / "config.yaml"
            config_file.write_text(
                "data: {month: '2026-01'}\ngrid: {size_meters: 3000, geometry: hexagon, metric_crs: EPSG:2263}\nrandom_seed: 42\ntime: {interval_minutes: 30}\n",
                encoding="utf-8",
            )
            with self.assertRaisesRegex(ValueError, "square-grid"):
                load_config(config_file)
