# Dataset Card

Synthetic 2,700-row, one-second tablet-press stream for integration and evaluation. Labels: normal, compression-force high, weight variation, sticking/picking proxy, and vibration/bearing. It is not real production data, does not establish real thresholds, and must not be used for LLM fine-tuning or production decisions. Use deterministic rules first; optional anomaly ML must train only on contiguous normal windows. The sticking/picking label is only a telemetry proxy requiring physical confirmation.
