# Source test gates

Run from a clean checkout in the reviewed configured Python environment, with Node and required parser artifacts available. No network collection or deployment is part of these commands. Missing prerequisites are unverified, not passed.

The gate at source base 20649f625838f74a429b61702c9d9a8e2fdaca84 passed 1469 root + 285 collectors + 10 checks + 26 world cases, with 2 skips and 1 expected failure. The staging manifest records only the root count. Counts are measured, not permanent targets.

```bash
PYTHONPATH=.:collector108_prep python -m unittest discover -s tests
PYTHONPATH=.:collector108_prep python -m unittest collector108_prep.test_durable \
  collector108_prep.test_job_contract collector109_prep.test_drive collector109_prep.test_engine_chain \
  collector109_prep.test_fetch_stage collector109_prep.test_safety collector109_prep.wiring.test_endpoint_drive \
  collector110_prep.test_durable_checkpoint collector110_prep.test_input_budget collector111_prep.test_drive \
  collector111_prep.test_drive_durable collector111_prep.test_engine_chain collector111_prep.test_safety \
  collector112_prep.test_parser collector113_prep.test_composition collector113_prep.test_transport \
  collector114_prep.test_connector collector114_prep.test_runner collector115_prep.test_composition \
  collector115_prep.test_profile collector116_prep.test_network_selection collector117_prep.test_supplied_cycle \
  collector118_prep.test_fulltext_composition collector119_prep.test_fulltext_composition collector120_prep.test_gnews_supplied \
  collector121_prep.test_telegram_supplied collector123_prep.test_budget collector124_prep.test_framing \
  collector124_prep.test_runner collector125_prep.test_budget collector126_prep.test_profile \
  collector127_prep.test_budget collector127_prep.test_extras collector128_prep.test_projection \
  collector129_prep.test_selection collector130_prep.test_composition
PYTHONPATH=.:collector108_prep python -m unittest discover -s checks
PYTHONPATH=.:collector108_prep python -m unittest feature_world_views.test_detail \
  feature_world_views.test_export feature_world_views.test_filters feature_world_views.test_inventory \
  feature_world_views.test_world
```

For named case discovery, use the same unittest loader and print each case's `id()` before execution. Root `discover -s tests` does not include the collector, checks or world blocks above. Keep their results separate. A full source gate is not a certificate of production settings, credentials, topology, current data or live readiness.
