# Installing QROS for Claude Code

Install QROS as a Claude Code plugin for stage-gated quantitative research workflows.

## Prerequisites

- Claude Code CLI
- Git

## Installation

Add the QROS marketplace, then install the plugin:

```
/plugin marketplace add web3qt/quant-research-os
/plugin install quant-research-os@qros
```

## Verify

Start a new Claude Code session and mention a quantitative research idea. QROS skills should activate automatically.

You can also explicitly trigger the research session:

```
qros-research-session 帮我研究这个想法：BTC 领动高流动性 ALT
```

## Manual Runtime Setup (Optional)

If you want access to the CLI tools (`qros-session`, `qros-review`) outside of Claude Code:

```bash
git clone https://github.com/web3qt/quant-research-os.git ~/.qros
cd ~/.qros && ./setup
```

## Updating

```
/plugin update quant-research-os@qros
```

Or if using manual clone:

```bash
cd ~/.qros && git pull
```

## Uninstalling

```
/plugin uninstall quant-research-os@qros
```
