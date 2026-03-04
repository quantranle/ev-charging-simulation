from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

from src.charging_simulator import (
    simulate_rule_based_smart_charging,
    simulate_uncontrolled_charging,
)
from src.metrics import calculate_fleet_metrics
from src.profile_generator import generate_ev_profiles, validate_profiles
from src.tariff import create_time_of_use_tariff, calculate_total_charging_cost


def save_profile_plots(profiles_df, figures_dir: Path) -> None:
    figures_dir.mkdir(parents=True, exist_ok=True)

    plt.figure(figsize=(8, 4))
    plt.hist(
        profiles_df["arrival_hour"], bins=range(0, 25), edgecolor="black", align="left"
    )
    plt.xticks(range(0, 24))
    plt.xlabel("Arrival Hour")
    plt.ylabel("Number of EVs")
    plt.title("EV Arrival Hour Distribution (Synthetic Profiles)")
    plt.tight_layout()
    plt.savefig(figures_dir / "arrival_hour_histogram.png", dpi=150)
    plt.close()

    plt.figure(figsize=(8, 4))
    plt.hist(profiles_df["energy_needed_kwh"], bins=10, edgecolor="black")
    plt.xlabel("Energy Needed (kWh)")
    plt.ylabel("Number of EVs")
    plt.title("Energy Needed Distribution (Synthetic Profiles)")
    plt.tight_layout()
    plt.savefig(figures_dir / "energy_needed_histogram.png", dpi=150)
    plt.close()


def save_uncontrolled_load_plot(fleet_load_df, figures_dir: Path) -> None:
    plt.figure(figsize=(9, 4.5))
    plt.plot(fleet_load_df["hour"], fleet_load_df["fleet_load_kw"], marker="o")
    plt.xticks(range(0, 24))
    plt.xlabel("Hour of Day")
    plt.ylabel("Fleet Charging Load (kW)")
    plt.title("Uncontrolled EV Charging - Aggregate Fleet Load")
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(figures_dir / "aggregate_load_uncontrolled.png", dpi=150)
    plt.close()


def save_comparison_plot(load_a, load_b, labels, figures_dir: Path, filename: str) -> None:
    plt.figure(figsize=(9, 4.5))
    plt.plot(load_a["hour"], load_a["fleet_load_kw"], marker="o", label=labels[0])
    plt.plot(load_b["hour"], load_b["fleet_load_kw"], marker="o", label=labels[1])
    plt.xticks(range(0, 24))
    plt.xlabel("Hour of Day")
    plt.ylabel("Fleet Charging Load (kW)")
    plt.title("Fleet Load Comparison")
    plt.grid(True, alpha=0.3)
    plt.legend()
    plt.tight_layout()
    plt.savefig(figures_dir / filename, dpi=150)
    plt.close()


def save_load_and_tariff_plot(fleet_unctrl, fleet_smart, tariff_df, figures_dir: Path) -> None:
    fig, ax1 = plt.subplots(figsize=(10, 5))

    ax1.plot(fleet_unctrl["hour"], fleet_unctrl["fleet_load_kw"], marker="o", label="Uncontrolled")
    ax1.plot(fleet_smart["hour"], fleet_smart["fleet_load_kw"], marker="o", label="Smart (Rule-based)")
    ax1.set_xlabel("Hour of Day")
    ax1.set_ylabel("Fleet Charging Load (kW)")
    ax1.set_xticks(range(0, 24))
    ax1.grid(True, alpha=0.3)

    ax2 = ax1.twinx()
    ax2.plot(
        tariff_df["hour"],
        tariff_df["price_eur_per_kwh"],
        linestyle="--",
        marker="s",
        label="Tariff (EUR/kWh)",
    )
    ax2.set_ylabel("Tariff (EUR/kWh)")

    lines1, labels1 = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax1.legend(lines1 + lines2, labels1 + labels2, loc="upper left")

    plt.title("Fleet Load and Time-of-Use Tariff")
    plt.tight_layout()
    plt.savefig(figures_dir / "fleet_load_and_tariff_comparison.png", dpi=150)
    plt.close()


def main() -> None:
    output_dir = Path("results")
    figures_dir = output_dir / "figures"
    output_dir.mkdir(parents=True, exist_ok=True)
    figures_dir.mkdir(parents=True, exist_ok=True)

    profiles_df = generate_ev_profiles(n_evs=50, seed=42)
    validate_profiles(profiles_df)

    profiles_path = output_dir / "ev_profiles_day1.csv"
    profiles_df.to_csv(profiles_path, index=False)

    save_profile_plots(profiles_df, figures_dir)

    charging_power_kw = 7.0
    peak_hours = [16, 17, 18]

    fleet_unctrl, ev_unctrl = simulate_uncontrolled_charging(
        profiles_df=profiles_df,
        charging_power_kw=charging_power_kw,
    )

    fleet_smart, ev_smart = simulate_rule_based_smart_charging(
        profiles_df=profiles_df,
        charging_power_kw=charging_power_kw,
        peak_hours=peak_hours,
    )

    tariff_df = create_time_of_use_tariff()
    tariff_df.to_csv(output_dir / "tariff_schedule.csv", index=False)

    cost_unctrl = calculate_total_charging_cost(fleet_unctrl, tariff_df)
    cost_smart = calculate_total_charging_cost(fleet_smart, tariff_df)

    metrics_unctrl = calculate_fleet_metrics(fleet_unctrl, ev_unctrl, total_cost_eur=cost_unctrl)
    metrics_smart = calculate_fleet_metrics(fleet_smart, ev_smart, total_cost_eur=cost_smart)

    fleet_unctrl.to_csv(output_dir / "fleet_load_uncontrolled.csv", index=False)
    ev_unctrl.to_csv(output_dir / "ev_results_uncontrolled.csv", index=False)

    fleet_smart.to_csv(output_dir / "fleet_load_smart_rule_based.csv", index=False)
    ev_smart.to_csv(output_dir / "ev_results_smart_rule_based.csv", index=False)

    save_uncontrolled_load_plot(fleet_unctrl, figures_dir)
    save_comparison_plot(
        fleet_unctrl,
        fleet_smart,
        labels=["Uncontrolled", "Smart (Rule-based)"],
        figures_dir=figures_dir,
        filename="fleet_load_comparison_uncontrolled_vs_smart.png",
    )
    save_load_and_tariff_plot(fleet_unctrl, fleet_smart, tariff_df, figures_dir)

    merged = profiles_df.merge(
        ev_unctrl, on=["ev_id", "arrival_hour", "departure_hour", "energy_needed_kwh"]
    )
    merged["max_possible_energy_kwh"] = merged["available_hours"] * charging_power_kw
    merged["feasible"] = merged["energy_needed_kwh"] <= merged["max_possible_energy_kwh"] + 1e-9

    not_completed = merged[merged["completed"] == False].copy()

    metrics_df = pd.DataFrame(
        [
            {"scenario": "uncontrolled", **metrics_unctrl},
            {"scenario": "smart_rule_based", **metrics_smart},
        ]
    )
    metrics_df.to_csv(output_dir / "metrics_comparison_day4.csv", index=False)

    print("=== Day 4: Cost-aware comparison ===")
    print(f"Profiles saved: {profiles_path}")
    print("Peak avoidance hours:", peak_hours)
    print()

    print("Uncontrolled metrics:")
    for k, v in metrics_unctrl.items():
        print(f" - {k}: {v}")
    print()

    print("Smart (rule-based) metrics:")
    for k, v in metrics_smart.items():
        print(f" - {k}: {v}")
    print()

    cost_saving = cost_unctrl - cost_smart
    cost_saving_pct = (cost_saving / cost_unctrl * 100) if cost_unctrl > 0 else 0.0

    print("Cost comparison:")
    print(f" - uncontrolled_cost_eur: {round(cost_unctrl, 2)}")
    print(f" - smart_cost_eur: {round(cost_smart, 2)}")
    print(f" - cost_saving_eur: {round(cost_saving, 2)}")
    print(f" - cost_saving_pct: {round(cost_saving_pct, 2)}")
    print()

    print("=== Root-cause: Incomplete EVs (Uncontrolled) ===")
    print("Not completed EVs:", len(not_completed))
    print("Not completed but feasible (should be near 0):", int(not_completed["feasible"].sum()))


if __name__ == "__main__":
    main()