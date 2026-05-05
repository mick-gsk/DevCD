# Research Continuity Demo

This synthetic demo is the first non-developer continuity fixture for DevCD. It shows how a new AI research agent could continue a multi-source research workflow from metadata-only local events after chat context is lost.

## Scenario

A user is researching whether retrieval latency changes answer quality in multi-source research agents. The first agent reviewed two synthetic sources, formed a hypothesis, tried a comparison, and found that the comparison failed because source set size was not controlled. Then chat context was lost.

The next agent must know the research goal, reviewed source metadata, current hypothesis, attempted approach, failed approach, do-not-repeat instruction, withheld context, and next step without seeing full source text or private note content. The fixture uses hand-written JSONL events; it does not implement browser, note, or library connectors.

## Run

```bash
devcd context handoff-demo --events examples/research-continuity/sample-events.jsonl --surface research-agent --pack research
```

PowerShell uses the same command from the repository root.

## Files

- `sample-events.jsonl`: synthetic local DevCD events.
- `without-devcd.md`: baseline when the next agent has no continuity packet.
- `with-devcd.md`: what changes when DevCD provides the packet.
- `continuity-packet.md`: expected CLI output generated from the fixture.

## Policy Safety

The fixture intentionally includes a full-text note payload and a private browser URL. The default policy withholds both from the packet and exposes only safe summaries. Reviewed sources are represented as metadata only.
