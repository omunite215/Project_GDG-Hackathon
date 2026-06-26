# lessons.md — mistakes & the rules we learned

Format: each entry = **what went wrong → the rule**. Add a matching one-line guard to `CLAUDE.md` → "Guards". Carry this file into the next project so the agent doesn't repeat the same mistakes.

## Seeded lessons (from planning)
1. **Misread the task as ML training.** Seeing "Gemma" triggered reaching for hyperparameter tuning / early stopping / CUDA training. → **Rule:** classify the task type first. This is *inference + prompt engineering*; the GPU only speeds inference.
2. **Almost hand-rolled regex JSON parsing + repair as the primary path.** → **Rule:** use Ollama structured outputs (`format=schema`, `temperature=0`). Constrained decoding makes invalid JSON impossible and is ~6× faster; regex repair is at most a bounded fallback.
3. **Original brief carried a "PR creator/merger" framing that belongs to a different track.** → **Rule:** scope to the actual track (log triage); don't build features the rubric doesn't ask for.
4. **Almost split work as "AI part vs Gemma part" — a false split** (Gemma *is* the AI). → **Rule:** divide along the pipeline (data → model → emit) and keep the AI/ML person on the prompt/schema/eval core.

## Session lessons
- _<append here: date — what went wrong — the rule>_
