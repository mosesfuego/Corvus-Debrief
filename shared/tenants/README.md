# Tenant Profiles

This folder is the local development stand-in for future Corvus Cloud tenants.

Each prospective customer can have a private profile:

```text
shared/tenants/
  aerocore/
    onboarding.yaml
    reports/
    memory/log.json
    uploads/
```

The onboarding wizard should eventually write `onboarding.yaml` here for local
development, while a hosted SaaS version would store the same data in a
tenant-scoped database row.

Customer-specific profiles, reports, memory, and uploads are intentionally
ignored by git.
