# Demo Vulnerable FastAPI App

This repo generates a signed, attested image in GHCR for testing the
`ZeroTrustApplication` / `SupplyChainAttestation` Operators. The CI/CD pipeline is
**modular**: a thin orchestrator (`ci-cd.yaml`) wires single-job *reusable
workflows* (`job-*.yml`).

## Application endpoints

* `GET /health`, `/healthz`, `/healthy` — liveness.
* `GET /users/search?username=` — **intentionally vulnerable** (SQL injection) demo path.
* `POST /debug/eval` — **intentionally vulnerable** (eval/RCE) demo path.
* `POST /stats` — clean compute endpoint (`count/sum/mean/min/max`), exercised by the unit tests.

> The vulnerable endpoints are deliberate — this is the "vulnerable" sample used to
> show Trivy/VEX and admission behaviour. Never deploy this image for real.

## What the pipeline produces

The pipeline (`.github/workflows/ci-cd.yaml` + `job-*.yml`) runs, in order:

1. **`build-metadata`** — `compileall` lint surrogate → `vbbi-lint` artifact.
2. **`unit-tests`** — real `pytest` suite → `vbbi-test` artifact. **Gates the build**
   (`build-push` depends on it): a failing test stops the pipeline. Test deps live in
   `requirements-dev.txt` only — never in the Dockerfile, so the image SBOM/CVE
   posture is unchanged.
3. **`security-scan`** — OSS "Snyk-style" pre-build scan on source: **gitleaks**
   (secrets — **BLOCKING**; `build-push` depends on it, so a committed secret is
   never built into an image), **Semgrep** (SAST), **checkov** (Dockerfile +
   manifests IaC). Raw reports → `secscan-raw` artifact. Runs no cosign (no new
   keyless identity).
4. **`build-push`** — Docker build & push to `ghcr.io`; emits `image_repo` + `image_digest`.
5. **`scan-image`** — Trivy scan (`aquasecurity/trivy-action@v0.36.0`, trivy `v0.71.0`;
   non-blocking in demo mode: reports `HIGH`/`CRITICAL` without failing; set
   `exit-code: 1` for production).
6. **`attestations`** — Syft SBOM (`spdxjson`), OpenVEX, VBBI voucher (HMAC chain +
   Merkle root), ZTA policy attestation, the **`security-scan/v1`** attestation
   (`SabinGhost19/security-scan-attestorAction@v1.0.1` normalizes the `secscan-raw`
   reports into a signed predicate), and a cosign verify of all of them.
7. **`slsa-provenance`** — official SLSA v1.0 container provenance (external reusable workflow).
8. **`sign-verify`** — cosign keyless image signature + self-verify.
9. **`bump-manifests`** — GitOps push-back of the new digest into the manifests repo
   (only on push to `main`).

Every job runs `step-security/harden-runner` (audit, pinned by commit-SHA) as its
first step. The image runs non-root (`USER appuser`), compatible with `runAsNonRoot: true`.

## Keyless identity (cosign SAN)

Because cosign runs **inside** the reusable workflows, the Fulcio certificate
identity is the `job-*.yml` path, not `ci-cd.yaml`. Use these in the ZTA/SCA
`trustedIssuers`:

```text
# attestations (SBOM / OpenVEX / VBBI / ZTA-policy)
https://github.com/<ORG_OR_USER>/<REPO>/.github/workflows/job-attestations.yml@refs/heads/main
# image signature
https://github.com/<ORG_OR_USER>/<REPO>/.github/workflows/job-sign-verify.yml@refs/heads/main
```

The SLSA provenance keeps the official generator's identity and is verified
separately via `slsaProvenancePolicy.trustedIssuers`.

## 1) Create a repository on GitHub

Example repo name: `demo-vulnerable-fastapi` (remote: `vulfastapi`).

## 2) Push local content

```bash
cd /home/sabinghosty19/Desktop/LICENTA/customCRD/demo-repos-apps/demo-app
git init && git add . && git commit -m "demo app + modular supply-chain CI/CD"
git branch -M main
git remote add origin git@github.com:<ORG_OR_USER>/<REPO>.git
git push -u origin main
```

Secrets to set: `VBBI_HMAC_KEY`, `MANIFESTS_REPO_TOKEN`.

## 3) Run the workflow

Runs automatically on push to `main`. Watch the jobs in GitHub Actions; the
reusable workflows appear as separate entries invoked via `workflow_call`.

## 4) Extract values for the CRDs

From the Job Summary: `IMAGE_REF`, `VBBI_MERKLE_ROOT`, `COMPUTED_INFRA_HASH`, plus
the identities above for `trustedIssuers`.

## 5) Run tests locally (optional)

```bash
pip install -r requirements.txt -r requirements-dev.txt
pytest -q
```

## 6) Run the app locally (optional)

```bash
docker build -t demo-vuln-fastapi:local .
docker run --rm -p 8080:8080 demo-vuln-fastapi:local
curl http://localhost:8080/health
curl -X POST localhost:8080/stats -H 'content-type: application/json' -d '{"values":[2,4,6,8]}'
```

Use immutable references (`@sha256:...` or `:vN.N.N`); never `latest`.

## Manifests

The GitOps manifests live in `SabinGhost19/vulfastapi-manifests-samples` (mirrored
locally as `demo-repos-apps/manifests-demo-app/`, sub-path `demo-app/`).
