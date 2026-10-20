"""Reproduce two Palmer Penguins figures and a machine-readable summary."""
from __future__ import annotations

import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data" / "penguins.csv"
FIGURES = ROOT / "figures"
FIGURES.mkdir(exist_ok=True)

PALETTE = {
    "Adelie": "#18779A",
    "Chinstrap": "#D77B31",
    "Gentoo": "#8064B0",
}
ORDER = ["Adelie", "Chinstrap", "Gentoo"]

def main() -> None:
    raw = pd.read_csv(DATA)
    required = {"species", "flipper_length_mm", "body_mass_g"}
    if not required.issubset(raw.columns):
        raise ValueError(f"Missing columns: {required - set(raw.columns)}")

    clean = raw.dropna(subset=["species", "flipper_length_mm", "body_mass_g"]).copy()
    clean = clean.loc[clean["species"].isin(ORDER)]
    for col in ("flipper_length_mm", "body_mass_g"):
        clean[col] = pd.to_numeric(clean[col], errors="coerce")
    clean = clean.dropna(subset=["flipper_length_mm", "body_mass_g"])
    if clean.empty:
        raise ValueError("No complete observations remain.")

    summary = {
        "raw_rows": int(len(raw)),
        "complete_rows": int(len(clean)),
        "missing_excluded": int(len(raw) - len(clean)),
        "overall_spearman": round(float(clean["flipper_length_mm"].corr(
            clean["body_mass_g"], method="spearman")), 3),
        "by_species": {},
    }
    for species in ORDER:
        group = clean.loc[clean["species"] == species]
        summary["by_species"][species] = {
            "count": int(len(group)),
            "median_flipper_mm": float(group["flipper_length_mm"].median()),
            "median_mass_g": float(group["body_mass_g"].median()),
            "spearman": round(float(group["flipper_length_mm"].corr(
                group["body_mass_g"], method="spearman")), 3),
        }

    sns.set_theme(style="whitegrid", context="talk", font_scale=.83)
    fig, ax = plt.subplots(figsize=(10, 6), dpi=160)
    sns.boxplot(data=clean, x="species", y="flipper_length_mm", order=ORDER,
                hue="species", palette=PALETTE, legend=False, width=.55,
                showfliers=False, ax=ax)
    np.random.seed(42)  # Keep point jitter identical between runs.
    sns.stripplot(data=clean, x="species", y="flipper_length_mm", order=ORDER,
                  color="#263544", alpha=.24, size=3, jitter=.22, ax=ax)
    for x, species in enumerate(ORDER):
        median = summary["by_species"][species]["median_flipper_mm"]
        count = summary["by_species"][species]["count"]
        ax.text(x, 244, f"median {median:.0f} mm\nn={count}",
                ha="center", va="top", fontsize=10, fontweight="bold")
    ax.set(title="Gentoo penguins have longer flippers in this sample",
           xlabel="Species", ylabel="Flipper length (mm)", ylim=(169, 250))
    sns.despine(ax=ax)
    fig.tight_layout()
    fig.savefig(FIGURES / "flipper_length_by_species.png", bbox_inches="tight")
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(10, 6), dpi=160)
    sns.scatterplot(data=clean, x="flipper_length_mm", y="body_mass_g",
                    hue="species", hue_order=ORDER, palette=PALETTE,
                    s=55, alpha=.72, edgecolor="white", linewidth=.35, ax=ax)
    sns.regplot(data=clean, x="flipper_length_mm", y="body_mass_g",
                scatter=False, ci=None, color="#32414A",
                line_kws={"linestyle": "--", "linewidth": 2}, ax=ax)
    ax.set(title="Longer flippers tend to accompany greater body mass",
           xlabel="Flipper length (mm)", ylabel="Body mass (g)")
    ax.legend(title="Species", loc="upper left", frameon=True)
    ax.text(.98, .04,
            f"Overall Spearman ρ = {summary['overall_spearman']:.2f}\n"
            "Observational association, not causation",
            transform=ax.transAxes, ha="right", va="bottom", fontsize=10,
            bbox={"facecolor": "white", "edgecolor": "#ccd5dd", "alpha": .95})
    sns.despine(ax=ax)
    fig.tight_layout()
    fig.savefig(FIGURES / "flipper_length_vs_body_mass.png", bbox_inches="tight")
    plt.close(fig)

    (ROOT / "results.json").write_text(
        json.dumps(summary, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(summary, indent=2))

if __name__ == "__main__":
    main()
