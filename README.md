# Demo Vulnerable FastAPI App

This repo is used to generate a signed image in GHCR for testing the `ZeroTrustApplication` Operator.

## What the pipeline produces

* Build Docker image
* Push to `ghcr.io`
* Trivy scan (non-blocking în modul demo curent; raportează `HIGH`/`CRITICAL` fără fail)
* Cosign keyless signing
* Self-verify Cosign
* Output with `IMAGE_REF` and `SIGNER`
* Image runtime non-root (`USER appuser`) compatibil cu `runAsNonRoot: true`

Notă: pentru mod strict (production-like), setează `exit-code: 1` în workflow-ul `ci-cd.yaml`.
## 1) Create a repository on GitHub

Example repo name: `demo-vulnerable-fastapi`

## 2) Copy local content to the repo

From `customCRD/demo-app`:

```bash
cd /home/sabinghosty19/Desktop/LICENTA/customCRD/demo-app
git init
git add .
git commit -m "Initial demo app with CI/CD supply-chain"
git branch -M main
git remote add origin git@github.com:<ORG_OR_USER>/<REPO>.git
git push -u origin main

```

## 3) Run the workflow

* Runs automatically on push to `main`.
* Check the `build-scan-sign` job in GitHub Actions.

## 4) Extract values for the ZTA CRD

From the Job Summary:

* `IMAGE_REF` (ideal for immutable reference)
* `SIGNER`

The `SIGNER` must be used in the ZTA:

```text
https://github.com/<ORG_OR_USER>/<REPO>/.github/workflows/ci-cd.yaml@refs/heads/main

```

## 5) Tag variant (without digest)

If you keep strictly immutable tags, you can use:

```text
ghcr.io/<ORG_OR_USER>/demo-vulnerable-fastapi:v1.0.0
ghcr.io/<ORG_OR_USER>/demo-vulnerable-fastapi:v1.0.1
ghcr.io/<ORG_OR_USER>/demo-vulnerable-fastapi:v1.0.2

```

Do not use `latest`.

## 6) Test the app locally (optional)

```bash
docker build -t demo-vuln-fastapi:v1.0.2 .
docker run --rm -p 8080:8080 demo-vuln-fastapi:v1.0.2
curl http://localhost:8080/health

```

