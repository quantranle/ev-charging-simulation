from pathlib import Path

import matplotlib.pyplot as plt

from src.profile_generator import generate_ev_profiles, validate_profiles


def save_day1_plots(df, figures_dir: Path) -> None:
    figures_dir.mkdir(parents=True, exist_ok=True)

    # Arrival hour histogram
    plt.figure(figsize=(8, 4))
    plt.hist(df["arrival_hour"], bins=range(0, 25), edgecolor="black", align="left")
    plt.xticks(range(0, 24))
    plt.xlabel("Arrival Hour")
    plt.ylabel("Number of EVs")
    plt.title("EV Arrival Hour Distribution (Day 1 Synthetic Profiles)")
    plt.tight_layout()
    plt.savefig(figures_dir / "arrival_hour_histogram.png", dpi=150)
    plt.close()

    # Energy needed histogram
    plt.figure(figsize=(8, 4))
    plt.hist(df["energy_needed_kwh"], bins=10, edgecolor="black")
    plt.xlabel("Energy Needed (kWh)")
    plt.ylabel("Number of EVs")
    plt.title("Energy Needed Distribution (Day 1 Synthetic Profiles)")
    plt.tight_layout()
    plt.savefig(figures_dir / "energy_needed_histogram.png", dpi=150)
    plt.close()


def main() -> None:
    output_dir = Path("results")
    figures_dir = output_dir / "figures"
    output_dir.mkdir(parents=True, exist_ok=True)

    df = generate_ev_profiles(n_evs=50, seed=42)
    validate_profiles(df)

    output_path = output_dir / "ev_profiles_day1.csv"
    df.to_csv(output_path, index=False)

    save_day1_plots(df, figures_dir)

    print("Generated EV profiles successfully.")
    print(f"Saved CSV to: {output_path}")
    print(f"Saved figures to: {figures_dir}")
    print()
    print(df.head(10).to_string(index=False))
    print()
    print("Quick summary:")
    print(df.describe())


if __name__ == "__main__":
    main()