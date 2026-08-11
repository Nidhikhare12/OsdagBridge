"""Serialization helpers for design ledgers."""

import json


def ledger_to_json(ledger, output_path):
    """
    Export a design ledger into JSON format.
    """

    with open(output_path, "w", encoding="utf-8") as file:
        json.dump(
            ledger.to_dict(),
            file,
            indent=4
        )


def ledger_to_dict(ledger):
    """
    Convert ledger contents into dictionary data.
    """

    return {
        "summary": ledger.summary(),
        "checks": ledger.to_dict(),
    }
