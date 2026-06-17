# Corpus

This directory contains processed FOIA/UAP documents for gap analysis.

## Format

Each document should be a JSON file with this structure:

```json
{
  "name": "AARO_2024_Q1_Release",
  "source": "https://aaro.mil/Portals/136/...",
  "date_released": "2024-01-15",
  "sections": [
    "Executive Summary",
    "Case Files",
    "Appendix A"
  ],
  "references": [
    [0, 1],
    [1, 2]
  ],
  "raw_text": "...",
  "submitted_by": "@researcher_handle"
}
```

## Contributing

PR your processed docs here. Name the file `[SOURCE]_[YEAR]_[DESCRIPTOR].json`.
Example: `AARO_2024_Q1_162docs.json`
