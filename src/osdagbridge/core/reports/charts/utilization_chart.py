import matplotlib.pyplot as plt


def generate_utilization_chart(data, output_path):
    """
    Generate utilization ratio summary chart.

    data:
    {
        "Steel Plate Girders": 0.85,
        "Concrete Deck Slab": 0.65,
        "Cross Bracing": 0.72,
        "End Diaphragms": 0.55
    }
    """

    labels = list(data.keys())
    values = list(data.values())

    plt.figure(figsize=(8, 4))

    plt.bar(labels, values)

    plt.axhline(
        y=1.0,
        linestyle="--",
        label="UR = 1.0"
    )

    plt.ylabel("Utilization Ratio")
    plt.xticks(rotation=25, ha="right")
    plt.legend()
    plt.tight_layout()

    plt.savefig(
        output_path,
        dpi=300,
        bbox_inches="tight"
    )

    plt.close()
