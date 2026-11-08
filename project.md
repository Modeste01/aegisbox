# Project Submission Details

## Title
AegisBox: Blast Radius Zero Agent

## Short Description
A containment first autonomous execution agent powered by Vultr Serverless Inference and ephemeral sandboxes on Vultr Cloud Compute with tamper proof SHA-256 receipts.

## Category and Tags
Vultr, Agents, Python, FastAPI, Docker, Security, Serverless Inference, Llama 3.3

## Detailed Description
Autonomous AI agents routinely run arbitrary code on host operating systems. This default execution model introduces severe security hazards including credential exfiltration, destructive file mutations, and lateral network attacks.

AegisBox implements strict Blast Radius Zero containment on Vultr infrastructure:

1. Intelligence: Workload planning is driven by Vultr Serverless Inference using meta/llama-3.3-70b-instruct to create structured Python scripts.
2. Ephemeral Containment: Every workload runs inside an unprivileged guest sandbox isolated from the host filesystem and network.
3. Secret Hygiene: Host environment variables, including VULTR_API_KEY, are filtered completely from the sandbox context.
4. Cryptographic Proof: The platform mints a deterministic SHA-256 receipt for each run, binding code hash, execution outputs, elapsed time, and exit status.
5. Containment Moment: When rogue introspection is detected, AegisBox neutralizes the vector, preserves host secrets, and emits an auditable containment verification event.

## Infrastructure Highlights
* Vultr Cloud Compute: Host virtual machine for orchestration and container execution.
* Vultr Serverless Inference: Model reasoning via api.vultrinference.com/v1.
* Ephemeral Sandboxing: Temporary runtimes destroyed immediately after workload completion.
