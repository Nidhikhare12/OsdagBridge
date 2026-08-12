
import matplotlib.pyplot as plt


def generate_material_chart(data, output_path):
    labels = list(data.keys())
    values = list(data.values())

    plt.figure(figsize=(7, 4))
    plt.bar(labels, values)
    plt.ylabel("Quantity")
    plt.xticks(rotation=25, ha="right")
    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches="tight")
    plt.close()
