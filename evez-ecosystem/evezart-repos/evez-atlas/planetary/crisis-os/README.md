# Crisis OS — Workstream A
**Module:** planetary/crisis-os | **Cadence:** Every 5 rounds | **Truth Plane:** CANONICAL

## Crisis Taxonomy
| Category | Leading Indicators | Threshold | Intervention Lever |
|----------|-------------------|-----------|-------------------|
| Climate | NOAA anomaly index, Copernicus CAMS | >2σ | Adaptation playbook |
| Health | WHO IHR events, GISAID variant rate | R>1.3 | Containment playbook |
| Conflict | ACLED event rate, displacement | +30% 30d | Mediation + aid routing |
| Energy | Grid frequency deviation, LNG spot | >15% | Demand response + reserves |
| Food/Water | FAO price index, drought monitor | >20% | Reserve release + aid |
| Cyber | CVE CVSS≥9 rate, CISA KEV count | >5/wk | Patch prioritization |
| Misinformation | Narrative velocity, source diversity | viral | Counter-narrative + label |
| Infrastructure | SCADA anomaly, bridge/dam sensors | critical | Emergency repair |
| Migration | UNHCR displacement rate | >100k/wk | Corridor + reception |
| Supply Chain | PMI, container rates, port congestion | 2mo lag | Diversification + buffer |

## Crisis Risk Index (CRI)
Formula: CRI = Σ(severity_i × trend_i × confidence_i) / N_categories
Range: 0.0 (stable) → 1.0 (critical)
Output: published to Ably `evez:crisis` channel per run

## Hotspot Object Model
```json
{
  "region": "string",
  "hazard_type": "climate|health|conflict|energy|food|cyber|misinfo|infra|migration|supply",
  "severity": 0.0,
  "trend": "rising|stable|falling",
  "confidence": 0.0,
  "evidence_links": [],
  "last_update": "ISO8601",
  "falsifier": "what would make this wrong"
}
```

## Ingestion Sources
- WHO IHR Event Information Site
- NOAA Climate.gov anomaly feeds
- Copernicus CAMS air quality + C3S climate
- ACLED conflict event database
- CISA Known Exploited Vulnerabilities (KEV) catalog
- FAO Food Price Index
- UNHCR displacement tracking
- IMF WEO + FSR for economic stress

## Deliverables
- `crisis_index.json` — updated per CRI run
- Vercel dashboard: evez-os/crisis (to deploy)
- Ably channel: `evez:crisis` realtime alerts
- GitHub: playbooks per hazard type (72h / 8wk / 24mo)

## Status
- Schema: DEFINED
- Ingestion: PENDING (Perplexity connector routes to go live)
- Dashboard: PENDING Vercel deploy
- Playbooks: PENDING first CRI run with live data
