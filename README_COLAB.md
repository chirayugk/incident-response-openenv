# Colab Run Guide

## Run order
1. Install dependencies cell
2. Script generation cells (`%%writefile`)
3. Execute commands below

## Commands
```bash
python test_env.py
python baseline_agent.py
python multi_agent_demo.py
python train_agent.py
```

## Multi-agent workflow
- Manager prioritizes and assigns tasks.
- Analyst (monitor role) scans logs and raises alerts.
- Responder (engineer role) mitigates and validates.

## Evaluation results
- Success rate
- Average reward
- Average steps to resolution
- Failed episodes saved to `failed_episodes.json`
