# QROS Codex Install

```bash
git clone <QROS_REPO_URL> ~/.codex/qros
mkdir -p ~/.agents/skills
ln -s ~/.codex/qros/skills ~/.agents/skills/qros
```

Update:

```bash
cd ~/.codex/qros
git pull
```

Codex discovers QROS through `~/.agents/skills/qros`, which should point at `~/.codex/qros/skills`.
