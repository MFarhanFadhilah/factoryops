# Proving It Works and Pitching It

Two jobs at the end of the day: a number that proves it works, and five minutes that make a judge care. Build the test set early, because it doubles as your demo script.

## Define "working" before you build it

- Pick 3-5 metrics, no more. Only the ones that would tell you the thing is broken if they moved. Candidates: task success rate, tool selection accuracy, wrong-answer rate, p95 latency, time saved per task vs. doing it by hand.
- Every metric gets a threshold written **before** you measure: "tool selection accuracy > 95%," "p95 under 3 seconds." Setting the bar after seeing the number is not measurement.
- Build a test set of at least 20 cases: happy paths, edge cases, and 3-5 adversarial ones (malformed input, ambiguous request, an attempt to push it out of scope). Format each as input, expected tool(s), expected output.
- Test components separately too - each tool with fixed inputs, then the whole loop end to end.
- Run the full set before the demo. If a metric misses, fix the build. Do not lower the threshold.
- If this replaces a manual process, run both on the same inputs and record the comparison. A side-by-side number is the strongest slide you will have.
- Write the numbers down as you go. At hour 11 there is no time to re-run anything.

## Build the argument before the slides

- One-sentence objective: "I want the judges to [conclude or do X] because [reason]." Can't fill all three blanks? You have a status update, not a pitch.
- Open with the setup: the situation they already accept, the complication that changed, the question that raises, then your one-sentence answer.
- Hang 3-5 supporting points under that answer. Each one answers a "how?" or "why?" the answer provokes. No more than five.
- Close on the specific ask, stated plainly.

## Slides

- Every headline is a full sentence with a verb and the insight. Not "Results" - "Local inference cut response time from 4 minutes to 8 seconds."
- Read only the headlines in order. If they tell the whole story with nothing else on screen, the deck works. If not, rewrite the headlines.
- One idea per slide. If you need "and" to describe a slide, split it.
- Max 5 bullets, fragments not sentences, under 75 words, understandable in 3 seconds.
- One bold color on the number that matters, grey for everything else. Highlight more than 10% of a slide and nothing is highlighted.
- Charts: bars for comparing amounts, lines for change over time. No pies, no gauges, no 3D. Never truncate an axis.
- Live demo beats a video beats screenshots. Record the fallback video before your slot anyway, and play it once to confirm it works.

## Eval

- Test cases in the set: target >= 20, including >= 3 adversarial
- Metrics defined with a numeric threshold written before measurement: target 3-5, all with thresholds
- Metrics below threshold at demo time: target 0
- Slides for a 5-minute pitch: target 5-7
- Slide headlines that are full sentences containing a verb: target 100%
- Slides that need "and" to describe: target 0
- Words on the busiest slide: target <= 75
- Fallback demo recording exists and has been played end to end once: pass/fail
