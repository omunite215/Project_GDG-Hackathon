"""Triage via local Gemma model.

Will call Ollama (gemma3:4b dev / gemma3:12b quality) with temperature=0 and
structured outputs (format=<schema>) to isolate the single anomalous/fatal line
and produce the validated TriageResult.

See docs/TRD.md (stack + contract).
"""

# TODO(phase-triage): call Ollama with format=schema, temperature=0, return TriageResult.
