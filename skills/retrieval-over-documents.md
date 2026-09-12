# Retrieval Over Documents

The agent's answers are only as good as what it retrieves. Retrieval is the build, not a supporting component, and it is the part most likely to look finished while being wrong. A confident wrong answer from a maintenance copilot is worse than no answer, because the technician acts on it.

## Tier the corpus before you ingest anything

Three tiers, and they are not interchangeable. Know which tier a given answer came from.

- **T1 manuals.** OEM fault tables, codes, thresholds, reset steps. Public, so everyone at the event can have them. Differentiates nothing on its own.
- **T2 repair logs.** Prior work orders on the same asset, in technician shorthand, uncleaned. Turns a code into a pattern: how often, and what it usually turned out to be. This is the first thing a manual cannot do.
- **T3 site notes.** Local, seasonal, conditional context about this installation. The only tier that answers a question about *this* machine, and the only one you can never own. That is the moat and it is worth saying out loud in the pitch.

If the demo only ever answers from T1, you built a PDF search box. The answer that wins is one that visibly combines tiers: the manual says this, the log says it was actually that four times out of five, and the site note explains why here.

## Chunk on structure, never on character count

- **Split on what the document actually is.** A fault table splits on table rows. A procedure splits on numbered steps. A work order splits on the record. Fixed-size character chunking cuts a fault code away from its threshold and its reset step, and then retrieval returns a row with no meaning.
- Keep the identifying key inside every chunk. A row that says "reset the breaker" without the fault code it belongs to is unretrievable and unciteable.
- Carry a small header on each chunk: equipment model, document title, section, page. This is what makes citation possible later, and citation is most of the trust.
- Handle tables before prose. The tables hold the answers, and they are what generic PDF extraction mangles first. Look at the extracted text of one real table with your eyes before you ingest three hundred pages on faith.
- T2 shorthand does not need cleaning. "ovrtmp trp, clnd fltr" is the signal. Normalising it into polished English throws away the vocabulary a technician will actually search with.

## Retrieve, then check what came back

- Start with plain keyword or BM25 search before anything embedding-based. On fault codes and part numbers, exact match beats semantic similarity outright, and it costs minutes instead of hours. Add embeddings only if you can show keyword failing on a real query.
- Retrieve a handful, not fifty. Every retrieved chunk is context budget, and a local model degrades faster from noise than it gains from coverage.
- If you use both keyword and semantic, decide the merge rule explicitly and write it down. "We combine them" is not a rule.

## Grounding is the whole product

- Every claim in an answer cites the chunk it came from, with the tier and the source header. No citation means the model generated it, and for this use case that is a defect, not a flourish.
- Instruct the model to say it does not know when retrieval comes back empty or off-topic. Then test that path deliberately, because it is the one that never gets tested by accident.
- Never let the model answer from its own training knowledge about equipment. Say so literally in the prompt: answer only from retrieved context. A plausible invented reset procedure is the failure mode that gets someone hurt, and it is the one a judge will probe.
- Show the retrieved chunks in the demo UI next to the answer. It makes grounding visible instead of claimed, and it doubles as your debugging view all day.

## Build order

1. Ingest five documents, not five hundred. Get one real query answering correctly end to end.
2. Look at the retrieved chunks by hand for that query. If they are wrong, no amount of prompt work fixes it.
3. Only then scale the corpus. Ingestion volume is the cheapest thing to add late and the most expensive thing to debug early.
4. Keep the ingest step rerunnable from scratch in one command. You will change the chunking rule at least twice.

## When retrieval is the problem

The symptom is a wrong or vague answer. Check in this order, and stop at the first failure:

1. **Is the fact in the corpus at all?** Grep the raw text. If it is not there, this is an ingestion problem, not a retrieval or prompt problem.
2. **Did extraction mangle it?** Look at the extracted text of that specific page. Tables are the usual culprit.
3. **Was it chunked apart?** Find the chunk holding the fact. If the fact and its key are in different chunks, fix the split rule.
4. **Did retrieval return it?** Print the retrieved chunks for the query. If the right chunk is not in the set, it is a retrieval problem.
5. **Only now is it the prompt.** The right chunk came back and the model still got it wrong.

Most teams start at step 5 and spend two hours there. The first four steps take ten minutes combined.

## Eval

- Tiers represented in the ingested corpus: target 3 of 3 (T1, T2, T3)
- Demo queries whose answer draws on more than one tier: target >= 1
- Chunks split on document structure rather than character count: target 100%
- Chunks carrying a source header (model, document, section, page): target 100%
- Answers in the test set containing a citation to a retrieved chunk: target 100%
- Answers containing a claim with no supporting retrieved chunk: target 0
- Empty-retrieval queries where the agent says it does not know instead of guessing: target 100%
- Retrieved chunks per query: target <= 8
- Documents ingested before the first correct end-to-end answer: target <= 5
- Time to rerun ingestion from scratch after a chunking change: target <= 5 min
- Minutes spent on prompt changes before checking whether the fact is in the corpus: target 0
