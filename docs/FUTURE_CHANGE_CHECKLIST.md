# Future Changes Checklist

> This document captures the **planned evolution** of the local LLM platform.  It serves as a living reference for developers, QA and operations teams.

## Overview
The platform is split into the following logical layers:
1. **Infrastructure** – Docker, MinIO, Chroma.
2. **Backend Services** – FastAPI gateway, MCP server, LSP bridge, LangGraph orchestration.
3. **Data & Storage** – Vector DB, object storage, embeddings.
4. **Client Interfaces** – Web UI (Next.js) and Swift macOS app.
5. **Observability & Security** – Logging, tracing, metrics, secrets management.

Each section lists *current state* and *future enhancements*.  The checklist is ordered by **dependency** – items that must be completed before the next can start.

---

## 1. Infrastructure Enhancements
| # | Task | Priority | Notes |
|---|------|----------|-------|
| 1.1 | Migrate MinIO to Kubernetes (kind) for local dev scalability | High | Allows volume snapshotting and multi‑node testing |
| 1.2 | Add Docker‑MPS client integration for GPU acceleration (Apple Silicon) | Medium | Enable `llama.cpp` with Metal support |
| 1.3 | Introduce Docker secrets for API keys & MinIO credentials | High | Replace `.env` in production |
| 1.4 | Implement automated backup of Chroma and MinIO volumes to S3‑compatible storage | Low | Long‑term data durability |

## 2. Backend Services
| # | Task | Priority | Notes |
|---|------|----------|-------|
| 2.1 | Refactor MCP to use gRPC instead of REST for lower latency | Medium | Useful for high‑frequency context updates |
| 2.2 | Add rate limiting middleware to FastAPI (e.g., `slowapi`) | High | Prevent abuse in shared environments |
| 2.3 | Extend LSP bridge to support additional languages (Rust, Go) via `pygls` plugins | Low | Future language support |
| 2.4 | Implement a fallback LLM (e.g., GPT‑Neo) when local model is unavailable | Medium | Increase reliability |
| 2.5 | Add audit logging of all LSP requests & tool executions | High | Compliance requirement |

## 3. Data & Storage
| # | Task | Priority | Notes |
|---|------|----------|-------|
| 3.1 | Replace Chroma with pgvector for production scalability (PostgreSQL + vector extension) | High | Enables sharding & replication |
| 3.2 | Add automatic re‑embedding pipeline triggered by file changes in MinIO bucket events | Medium | Keeps embeddings fresh |
| 3.3 | Implement per‑document versioning metadata in MinIO tags (e.g., `embedding_version`) | Low | Helps rollback embeddings |
| 3.4 | Benchmark embedding throughput on Apple Silicon (Metal) | Medium | Optimize performance |

## 4. Client Interfaces
| # | Task | Priority | Notes |
|---|------|----------|-------|
| 4.1 | Add authentication via macOS Keychain for Swift app, store API key securely | High | Security best practice |
| 4.2 | Implement streaming WebSocket for real‑time LLM responses in Next.js UI | High | Improves UX |
| 4.3 | Add file upload progress bar and chunked uploads to MinIO | Medium | Handles large files |
| 4.4 | Create a mobile‑friendly version of the web UI (React Native) | Low | Future expansion |

## 5. Observability & Security
| # | Task | Priority | Notes |
|---|------|----------|-------|
| 5.1 | Switch to OpenTelemetry Collector for unified tracing & metrics collection | High | Centralizes telemetry |
| 5.2 | Add Loki as log aggregator and Grafana dashboard for metrics | High | Real‑time monitoring |
| 5.3 | Implement automated security scanning (Trivy, Snyk) in CI pipeline | High | Detect vulnerabilities early |
| 5.4 | Add API key rotation mechanism via Docker secrets | Medium | Security hygiene |

---

## Roadmap Alignment
- **Phase 1**: Infrastructure & basic backend (tasks 1.1‑2.1).<br>
- **Phase 2**: Data layer upgrades & LSP extensions (tasks 3.1‑3.4, 2.2‑2.5).<br>
- **Phase 3**: Client UX improvements & observability (tasks 4.1‑5.2).<br>
- **Phase 4**: Security hardening & CI integration (tasks 5.3‑5.4).<br>

---

> **Note**: All tasks should be tracked in the main GitHub issue tracker and linked to the corresponding pull request.  Each PR must include unit tests, integration tests, and updated documentation.
