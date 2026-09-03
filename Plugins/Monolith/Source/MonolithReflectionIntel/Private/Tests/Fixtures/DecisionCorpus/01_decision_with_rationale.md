# Sample Spec 01

This is a sample spec used by automation tests.

## Adopt FSQLitePreparedStatement for all SQLite writes

We chose `FSQLitePreparedStatement` over raw `sqlite3_exec` because
the prepared-statement bind API gives us protection against
SQL-injection edge cases and the rationale captured in our
MeshCatalogIndexer audit (evidence: 60% fewer reflection roundtrips).

This decision should be ingested with the "because"/"evidence"
rationale markers and emit confidence >= 0.6.
