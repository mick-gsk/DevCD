# Research Continuity Demo

This synthetic demo is the first non-developer continuity fixture for DevCD. It shows how a new AI research agent could continue a multi-source research workflow from metadata-only local events after chat context is lost.

## Scenario

A user is researching whether retrieval latency changes answer quality in multi-source research agents. The first agent reviewed two synthetic sources, formed a hypothesis, tried a comparison, and found that the comparison failed because source set size was not controlled. Then chat context was lost.

The next agent must know the research goal, reviewed source metadata, current hypothesis, attempted approach, failed approach, do-not-repeat instruction, withheld context, and next step without seeing full source text or private note content. The checked-in continuity fixture still uses JSONL events so expected output remains stable, but a reusable local importer now exists for real local research-session exports.

## Run

```bash
devcd context handoff-demo --events examples/research-continuity/sample-events.jsonl --surface research-agent --pack research
```

To convert a local structured research export first:

```bash
devcd recipe research-session --input examples/event-source-recipes/research-session/input.json --output research-events.jsonl
devcd context handoff-demo --events research-events.jsonl --surface research-agent --pack research
```

PowerShell uses the same command from the repository root.

## Files

- `sample-events.jsonl`: synthetic local DevCD events.
- `without-devcd.md`: baseline when the next agent has no continuity packet.
- `with-devcd.md`: what changes when DevCD provides the packet.
- `continuity-packet.md`: expected CLI output generated from the fixture.
- `../event-source-recipes/research-session/input.json`: reusable local research-session recipe input.

## Policy Safety

The fixture intentionally includes a full-text note payload and a private browser URL. The default policy withholds both from the packet and exposes only safe summaries. The reusable research-session recipe follows the same boundary for raw note text, article text, transcript text, and full content. Reviewed sources are represented as metadata only.
