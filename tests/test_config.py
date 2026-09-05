"""Tests for first-milestone configuration contracts."""

from pathlib import Path
import tempfile
import unittest

import yaml

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
        self.assertEqual(config["pricing"]["customer_response_model"], "eq31")
        self.assertEqual(config["pricing"]["decision_mode"], "legacy_grid")
        self.assertEqual(config["pricing"]["sensitivity_fallback"], "error")
        self.assertEqual(config["pricing"]["reward_model"], "legacy_normalized_accepted_revenue")
        self.assertEqual(config["pricing"]["supply_model"], "legacy_all_statuses")

    def test_invalid_grid_geometry_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            config_file = Path(directory) / "config.yaml"
            config_file.write_text(
                "data: {month: '2026-01'}\ngrid: {size_meters: 3000, geometry: hexagon, metric_crs: EPSG:2263}\nrandom_seed: 42\ntime: {interval_minutes: 30}\n",
                encoding="utf-8",
            )
            with self.assertRaisesRegex(ValueError, "square-grid"):
                load_config(config_file)

    def test_request_8d_configuration_requires_corrected_supply_and_served_reward(self) -> None:
        config = yaml.safe_load(Path("config/config.yaml").read_text(encoding="utf-8"))
        config["pricing"].update({
            "decision_mode": "request_8d", "supply_model": "idle_plus_incoming",
            "reward_model": "served_dispatch_revenue", "sensitivity_fallback": "hierarchical",
        })
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "config.yaml"
            path.write_text(yaml.safe_dump(config), encoding="utf-8")
            self.assertEqual(load_config(path)["pricing"]["decision_mode"], "request_8d")
            config["pricing"]["supply_model"] = "legacy_all_statuses"
            path.write_text(yaml.safe_dump(config), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "idle_plus_incoming"):
                load_config(path)
            config["pricing"].update({
                "supply_model": "idle_plus_incoming",
                "reward_model": "legacy_normalized_accepted_revenue",
            })
            path.write_text(yaml.safe_dump(config), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "served_dispatch_revenue"):
                load_config(path)
