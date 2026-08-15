# SSH Runtime Files

`lab_config` is generated from `inventory/lab.yaml`.

`known_hosts` is local runtime SSH trust state and is intentionally not version controlled.

When device addresses or identities change, refresh the local known-host entries before running platform commands with strict host-key verification.
