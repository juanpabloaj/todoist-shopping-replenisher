# Phase 3 — Risk Note: Add Stronger HTTP Client Failure-Path Coverage

## Residual Issues

### 1. Tests exercise HTTP clients through mocked `urlopen` — not end-to-end network behavior
**Classification: accepted risk**
All four tests patch `request.urlopen` and do not exercise real network calls. They validate branch behavior and error translation, not actual HTTP transport.
**Phase 1 exclusion reference**: the contract brief states this is a test-only task covering existing branches in production code. Real network validation is out of scope by design — it would require live credentials and network access, which is inappropriate for a unit test suite.
**Why this still holds**: the production error-handling paths (`HTTPError`, `URLError`, `JSONDecodeError`, missing `id`) are deterministic code branches; mocking `urlopen` is the correct approach to test them in isolation.

### 2. Tests protect existing error message strings — wording changes require test updates
**Classification: accepted risk**
Each test asserts on a substring of the error message (e.g. `"JSON"`, `"ok"`, `"id"`). If the error message wording changes intentionally, the tests must be updated alongside.
**Phase 1 exclusion reference**: the contract brief explicitly requires assertions on message content to ensure mutation protection. This creates a coupling between test and message string that is intentional.
**Why this still holds**: message string coupling is the explicit requirement of the contract (mutation test standard). If messages change, tests should fail — that is the desired behavior, not a defect.
