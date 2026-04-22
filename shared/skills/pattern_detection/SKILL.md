# Pattern Detection Skill

## Purpose
Identify recurring signals across runs using memory log.

## When to use
- Agent reasoning over historical context
- Identifying systemic vs one-off issues

## Entry point
shared/memory/log.json

## Key behaviors
- Last 5 runs injected into agent context
- Recurring signals flagged as systemic
- Pattern note generated when same signal appears 3+ times

## Shared by
- Corvus Debrief
- (future) all Corvus MFG agents
