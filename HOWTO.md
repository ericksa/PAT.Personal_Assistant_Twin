# 📖 OpenCode Multi-Agent Orchestration Guide

This guide explains how to set up, use, and maintain the multi-agent orchestration system for the **PAT (Personal Assistant Toolkit)** project.

## 🚀 Quick Start

1. **Prerequisites**:
   - Install **Ollama** and ensure it's running (`ollama serve`).
   - (Optional) Install **LM Studio** and start the MLX server on your LAN.
   - Install **OpenCode CLI**: `npm install -g opencode-ai`.

2. **Environment Setup**:
   Set your API keys in your `.zshrc` or `.bashrc`:
   ```bash
   export LM_STUDIO_API_KEY="your-key-here"
   export DATABASE_URL="postgresql://user:pass@localhost:5432/pat_db"
   ```

3. **Verify Installation**:
   ```bash
   bash .opencode/verify-setup.sh
   ```

4. **Launch OpenCode**:
   ```bash
   opencode serve --port 4096
   ```

---

## 🤖 System Architecture

The system uses a **Master Orchestrator** (Primary Agent) that delegates tasks to **9 Domain Specialists** (Sub-agents).

### Specialist Agents

| Agent | Domain | Primary Model |
|-------|--------|---------------|
| `specialist-docker` | Containerization | `qwen3-coder` |
| `specialist-xcode` | macOS Development | `lmstudio-local` |
| `specialist-python` | Backend (FastAPI) | `qwen3-coder` |
| `specialist-frontend` | Web (Vue.js 3) | `qwen3-coder` |
| `specialist-docs` | Documentation | `gemma3` |
| `specialist-tdd` | Testing (pytest/Jest) | `qwen3-coder` |
| `specialist-security` | Vulnerability Scanning | `deepseek-v3.2` |
| `specialist-database` | PostgreSQL | `qwen3-coder` |
| `specialist-api` | API Design | `qwen3-coder` |

---

## ⚡ Usage Examples

### 1. Simple Feature Implementation
> **User**: "Add a new endpoint to list chat sessions."
> 
> **Orchestrator**:
> 1. Spawns `specialist-api` to design the endpoint.
> 2. Spawns `specialist-python` to implement the logic.
> 3. Spawns `specialist-tdd` to write tests.

### 2. Parallel Code Audit & Testing
> **User**: "Audit the authentication module and write missing tests."
> 
> **Orchestrator**: Spawns `specialist-security` and `specialist-tdd` in **parallel**.

---

## 🛡️ Security & Permissions

- **Local Inference**: All processing stays on your hardware (Ollama + LM Studio).
- **No Direct Internet**: All internet access (via `webfetch`) requires **explicit user approval**.
- **Write Approval**: Any file modification requires the agent to ask for permission.
- **Git Integration**: Agents can commit and push changes, but only after summarizing their work and getting your approval.
- **Audit Logs**: Key security actions are logged in the TUI session.

---

## 🛠️ Custom Tools

The system includes custom TypeScript tools in `.opencode/tools/`:
- `xcode.ts`: Automates building and testing macOS apps.
- `security-scanner.ts`: Scans for hardcoded secrets and insecure code patterns.
- `docker-helper.ts`: Monitors container health and resources.

---

## 🔄 Maintenance

### Adding a New Specialist
1. Create a config file in `.opencode/agents/specialist-[name].jsonc`.
2. Create a prompt file in `.opencode/prompts/[name].txt`.
3. Update the `orchestrator` permissions in `config.jsonc` to allow the new agent.

### Updating Models
Modify `.opencode/config.jsonc` to point specialists to new local models as they become available.

---

## ⚠️ Troubleshooting

- **Server Connection**: If OpenCode can't connect to Ollama, verify it's running on `localhost:11434`.
- **LM Studio**: Ensure the MLX server is enabled and the firewall allows traffic on port `1234`.
- **Parallelism**: If your system slows down, reduce `max_concurrent_agents` in `config.jsonc`.
