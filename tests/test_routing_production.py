"""Production initialization contracts for driver profiles and routing policy."""

from __future__ import annotations

import unittest
import inspect
import numpy as np
import pandas as pd

from src.charging.energy import EnergyParameters, requires_charging
from src.fleet.state import VehicleState, VehicleStatus
from src.routing.baseline import GridRoutingFeatures, RoutingAction, RoutingParameters, RoutingState, candidate_utility
from src.routing.learning import RoutingLearningParameters
from src.routing.production import (
    build_fare_bootstrap, generate_driver_profiles, initialize_common_policy_learners,
    initialize_nb9_fare_prior, normalized_dod_degradation_penalty,
    production_profile_utility_inputs, uniform_valid_action_probabilities,
)
from src.simulation.statistics import OperationalStatistics


class RoutingProductionTests(unittest.TestCase):
    def setUp(self) -> None:
        self.energy = EnergyParameters(75., 60., 7.5, .15, 30., .9, 75., .5, .05, .5, .7, .2)
        self.routing = RoutingParameters(15., 3., 30.)

    def test_normalized_dod_penalty_expected_soc_values_and_clipping(self) -> None:
        for soc, expected in ((1., 0.), (.8, .25), (.6, .5), (.4, .75), (.2, 1.)):
            self.assertAlmostEqual(normalized_dod_degradation_penalty(75. * soc, self.energy), expected)
        self.assertEqual(normalized_dod_degradation_penalty(10., self.energy), 1.)
        self.assertEqual(normalized_dod_degradation_penalty(75.0000001, self.energy), 0.)
        values = [normalized_dod_degradation_penalty(value, self.energy) for value in np.linspace(-10., 90., 101)]
        self.assertTrue(all(np.isfinite(value) and 0. <= value <= 1. for value in values))

    def test_source_equation_is_algebraically_equivalent(self) -> None:
        cbi, cycles, capacity, dod, power = 4000., 3000., 75., .8, 30.
        cbd_bac = cbi / (2. * cycles * capacity * dod)
        maximum = cbd_bac * ((capacity - capacity * .2) / power) * power
        for soc in (1., .8, .6, .4, .2):
            duration = (capacity - capacity * soc) / power
            source_ratio = cbd_bac * duration * power / maximum
            self.assertAlmostEqual(source_ratio, (1. - soc) / .8)
            self.assertAlmostEqual(source_ratio, normalized_dod_degradation_penalty(capacity * soc, self.energy))

    def test_runtime_inputs_use_current_and_post_move_energy(self) -> None:
        profiles = pd.DataFrame({"vehicle_id": [0], "price_preference": [20.], "wait_preference": [10.]})
        vehicle = VehicleState(0, 1, VehicleStatus.IDLE, None, 0., "idle", 45.)
        first = production_profile_utility_inputs(profiles, [vehicle], self.energy, self.routing)
        second = production_profile_utility_inputs(profiles, [vehicle], self.energy, self.routing)
        stay = first[0][RoutingAction.STAY].normalized_degradation_penalty
        move = first[0][RoutingAction.EAST].normalized_degradation_penalty
        self.assertAlmostEqual(stay, normalized_dod_degradation_penalty(45., self.energy))
        self.assertAlmostEqual(move, normalized_dod_degradation_penalty(45. - .45, self.energy))
        self.assertGreater(move, stay)
        self.assertEqual(first, second)

    def test_infeasible_vehicle_is_excluded_by_existing_energy_rule(self) -> None:
        vehicle = VehicleState(0, 1, VehicleStatus.IDLE, None, 0., "idle", .4)
        self.assertTrue(requires_charging(vehicle, self.energy))

    def test_helper_has_no_temperature_inputs_and_nb11_equation_is_unchanged(self) -> None:
        self.assertEqual(tuple(inspect.signature(normalized_dod_degradation_penalty).parameters), ("projected_energy_kwh", "energy"))
        features = GridRoutingFeatures(1, 1, 1, 1, 0, 0, 20., 5., 20., 5., 10., 5., 10., 5., True, 0.)
        item = production_profile_utility_inputs(
            pd.DataFrame({"vehicle_id": [0], "price_preference": [20.], "wait_preference": [10.]}),
            [VehicleState(0, 1, VehicleStatus.IDLE, None, 0., "idle", 45.)], self.energy, self.routing,
        )[0][RoutingAction.STAY]
        components = candidate_utility(features, item, 45., self.energy)
        self.assertAlmostEqual(components.total, (components.price + components.wait + components.charging) / 3.)

    def test_profiles_are_bounded_reproducible_and_cutoff_safe(self) -> None:
        trips = pd.DataFrame({
            "tpep_pickup_datetime": pd.to_datetime(["2026-01-01", "2026-01-02", "2026-01-25 18:30"], format="mixed"),
            "fare_amount": [10., 30., 1_000_000.],
        })
        first, stats = generate_driver_profiles(trips, range(5000), seed=42)
        same, same_stats = generate_driver_profiles(trips, range(5000), seed=42)
        other, _ = generate_driver_profiles(trips, range(5000), seed=43)
        self.assertEqual((len(first), first.vehicle_id.nunique(), first.vehicle_id.tolist()), (5000, 5000, list(range(5000))))
        pd.testing.assert_frame_equal(first, same)
        self.assertEqual(stats, same_stats)
        self.assertFalse(first[["price_preference", "wait_preference"]].equals(other[["price_preference", "wait_preference"]]))
        self.assertEqual((stats["fare_valid_row_count"], stats["mu_price"], stats["sigma_price"]), (2, 20., 10.))
        self.assertTrue(first.price_preference.between(stats["price_low"], stats["price_high"]).all())
        self.assertTrue(first.wait_preference.between(0, 30).all())

    def test_uniform_valid_probabilities_ignore_model_logits(self) -> None:
        feature = lambda grid: GridRoutingFeatures(grid, 1, 1, 1, 0, 0, 1, 0, 1, 0, None, None, None, None, False, 0)
        current = feature(0)
        state = RoutingState(0, 0, 40, current, {RoutingAction.STAY: current, RoutingAction.NORTH: feature(1), RoutingAction.EAST: None, RoutingAction.SOUTH: feature(2), RoutingAction.WEST: None})
        np.testing.assert_allclose(uniform_valid_action_probabilities(state), [1/3, 1/3, 0, 1/3, 0])

    def test_all_policy_models_share_one_exact_initialization(self) -> None:
        locals_, global_ = initialize_common_policy_learners(range(3), RoutingLearningParameters(), seed=42)
        reference = global_.policy_model.get_weights()
        for learner in locals_.values():
            self.assertTrue(all(np.array_equal(a, b) for a, b in zip(reference, learner.policy_model.get_weights())))

    def test_fare_bootstrap_is_pre_cutoff_grid_grouped_and_prior_only(self) -> None:
        trips = pd.DataFrame({
            "tpep_pickup_datetime": pd.to_datetime(["2026-01-01", "2026-01-02", "2026-01-03", "2026-01-25 18:30"], format="mixed"),
            "fare_amount": [10., 20., 30., 999999.], "PUGridID": [0, 0, 1, 0],
        })
        bootstrap, summary = build_fare_bootstrap(trips, [0, 1, 2])
        row0, row2 = bootstrap.set_index("grid_id").loc[0], bootstrap.set_index("grid_id").loc[2]
        self.assertEqual((row0.historical_fare_count, row0.mean_fare, row0.std_fare, row0.source_level), (2, 15., 5., "grid"))
        self.assertEqual((summary["global_valid_row_count"], summary["global_mean_fare"]), (3, 20.))
        self.assertEqual((row2.mean_fare, row2.std_fare, row2.source_level), (summary["global_mean_fare"], summary["global_std_fare"], "global_fallback"))
        statistics = OperationalStatistics([0, 1, 2], .3)
        initialize_nb9_fare_prior(statistics, bootstrap)
        empty = statistics.update_slot(0)
        self.assertTrue(all(row.fare_count == 0 and row.mean_fare is None for row in empty))
        self.assertEqual(empty[0].ewma_fare, 15.)


if __name__ == "__main__":
    unittest.main()
