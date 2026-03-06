class DebriefGenerator:
    def __init__(self, config):
        self.config = config

    def generate(self, analyzed_builds: list[dict]) -> str:
        """Stub — just formats builds as readable text for now."""
        lines = ["=== CORVUS DEBRIEF ===\n"]
        
        for build in analyzed_builds:
            lines.append(f"Build:         {build['build_id']}")
            lines.append(f"Station:       {build['station_id']}")
            lines.append(f"Status:        {build['status']}")
            lines.append(f"Completion:    {build['completion_pct']}%")
            lines.append(f"Duration:      {build['duration_hours']}hrs")
            lines.append(f"Delayed:       {build['delay_flag']}")
            lines.append(f"Notes:         {build.get('notes', '')}")
            lines.append("-" * 40)
        
        return "\n".join(lines)

    def output(self, debrief: str):
        """Print to console for MVP."""
        print(debrief)
