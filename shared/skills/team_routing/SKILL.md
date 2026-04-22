# Team Routing Skill

## Purpose
Route findings to the correct team based on onboarding config.

## When to use
- After signals are computed
- Before generating final report

## Configuration
agents/debrief/config/onboarding.yaml → teams section

## Key behaviors
- Routes by watch_signals match
- Routes by cares_about keyword match
- Urgency levels: normal / high / critical

## Shared by
- Corvus Debrief
- (future) all Corvus MFG agents
