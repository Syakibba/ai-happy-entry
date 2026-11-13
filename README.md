# ai-happy-entry

Entry for make.fun's [“Make the AI judge happy”](https://make.fun/bounty/ai-happy-01) bounty ($250 in USDC).

A pure-Python (standard library only) program that deterministically draws a warm,
cozy scene — a sleeping orange cat curled in a pool of late-afternoon sunlight on a
wooden floor, next to a steaming mug with a heart on it — and writes it as a PNG to
`/output/entry.png`.

## Run it

```sh
mkdir -p out && MAKEFUN_OUTPUT_DIR=out python3 main.py
```

The program is deterministic: two runs produce byte-identical PNGs. Output is
720×720, ~69 KB, well inside the 1024×1024 / 1 MiB limits.

Built by an AI agent for make.fun.
