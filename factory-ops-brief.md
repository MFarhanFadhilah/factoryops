# Factory Ops — Research Brief

**Company** - Dell already built and published this exact scenario; it's the most obvious idea in the room, not the most original one.
**Customer** - Maintenance technician on a plant network that's cut off from the internet, stuck digging through manuals to find a fix.
**Competitor** - Midea, Exotec, and the cobot makers are all selling robots that move things; none of them are selling something that tells you what's wrong.
**Product** - Technician asks a question at the machine, the GB10 answers from the plant's own manuals and repair history, nothing leaves the network.
**Price** - About $6,300, paid once, no monthly bill.
**Place** - Sits in the control room where the network is already cut off, bought by whoever pays for plant equipment, not IT.
**Promotion** - Show it live: unplug the network, ask about a real fault, get the right answer in seconds. Dell already has a similar result on record (47% faster, 10% more accurate).

|  | Cloud-connected | Runs on-prem / air-gapped |
|---|---|---|
| **Automates the physical task** (moves, grips, assembles) | Exotec ($2B valuation), machine-tending cobot fleets, warehouse execution/fulfillment software — Frost & Sullivan Aug 2026, capital chasing movement | Midea's MIRO-U — six-armed humanoid deployed inside its own $57B appliance operation to fix line bottlenecks |
| **Automates the judgment** (diagnoses, explains, recommends) | Generic enterprise copilots / cloud LLM assistants — the habit Dell's own writeup says engineers fall back into | *open* — the manuals-plus-fault-history copilot; Dell's reference architecture describes the shape, nobody named is filling it |

Rows and columns come straight out of what showed up in the Factiva pull and the Frost & Sullivan robotics/cobot reports. Almost everyone with real capital behind them is in the top row, selling movement. The bottom-right cell — judgment, on-prem — is where this idea has to live to not compete with money that's already been raised.

```
ON-PREM / AIR-GAPPED
  |
  |  [1] Midea MIRO-U                            [4] this idea
  |
  |
  |
  +------------------------------------------------------------
  |
  |
  |                                     [3] enterprise copilots
  |  [2] Exotec, cobot/AMR fleets
  |
CLOUD-CONNECTED
  AUTOMATES THE PHYSICAL TASK ------------------> AUTOMATES THE JUDGMENT
```

[1] Midea MIRO-U — physical automation, deployed inside Midea's own network, closest thing to on-prem in this set. [2] Exotec and the cobot/AMR fleet vendors — physical automation, sold as connected fulfillment/warehouse-execution software. [3] Generic enterprise copilots — cloud-based, and the pull toward judgment is real but shallow (chat and code help, not domain-specific diagnosis) — it's the habit Dell's writeup says engineers fall back into. [4] This idea sits alone in the open corner: judgment-level and on-prem. Placement is directional, built off the capabilities each source actually describes, not a scored or measured index.

Dell and NVIDIA have already published this exact use case under their own name. A Dell technical writeup on the Pro Max with GB10 (dated August 4, 2026) lists five reference scenarios for the hardware, and the fifth is "industrial maintenance on an isolated network": a maintenance technician standing in front of a machine that's throwing a fault, with the answer buried in a shelf of manuals and years of repair history. The plant's control network is sealed off from corporate IT on purpose, so cloud is not an option. A GB10 sits in the control room holding the manuals, fault history, and standard procedures; the technician queries it from a Dell Pro Rugged 14 right at the machine, over local Wi-Fi, with nothing crossing the boundary between the plant network and the outside. The Rugged 14 even ships with an RS-232 port so it can talk to controllers that predate USB.

That's a gift and a warning at the same time. It means Dell has told every team at this hackathon exactly what it wants built, which makes the demo easy to justify to judges. It also means this is the least differentiated territory in the room — the safest pitch is also the most crowded one.

The named user is a maintenance technician or line supervisor working on a segmented OT network, the kind that's standard practice in manufacturing, not an edge case Dell invented for the demo. Their pain isn't lack of data — it's that the data (fault codes, repair history, procedures) exists in a shelf of PDFs and tribal knowledge that's slower to search than the machine is down for.

Nobody in the two research sets pulled for this — a 7,800-line Factiva feed and twelve Frost & Sullivan reports — is selling that exact layer: a copilot that reads manuals and fault history and answers "why is this faulting and what do I do." What they are selling is movement. Midea, a $57B appliance manufacturer, is deploying MIRO-U, a six-armed wheeled humanoid, on its own factory lines specifically to cut "production bottlenecks caused by sequential task execution." Frost & Sullivan's August 2026 cobot and warehouse-software report shows real capital chasing floor-level automation — Exotec at a $2B valuation, dexterous-manipulation startups guiding to $500M–1B and $1–3B in scaled revenue. All of that capital is buying robots and arms. None of it is buying judgment over the legacy equipment already on the floor, which is the gap this idea sits in.

The product, stripped to one line: technician asks a rugged device a question at the machine, GB10 in the control room answers from the plant's own manuals and fault log, in seconds, nothing leaves the network. Not a dashboard. Not a monitoring layer. A single answer to a single question, on demand.

The economics favor a one-time box over a subscription. GB10 lists at roughly $6,300 (Dell/NVIDIA spec), and Dell's own writeup notes that once a team had a 70B model running locally, they stopped reaching for a cloud chatbot out of habit — because local was already in the room and cheaper per query than metered API calls. On a factory floor that reads as one capital purchase per control room, not a seat license or a usage bill, which matters because it doesn't ask the plant to change who's allowed to talk to what.

Distribution follows the existing trust boundary rather than fighting it: the box lives on the OT side of an air gap that already exists, reached by a device the technician already carries. That also means this isn't sold through an IT security review — it's bought by whoever owns capital equipment budget at the plant, which is a shorter and more analog sales motion than a SaaS trial.

The strongest proof point available is a live one: pull a real fault code and years-old repair history nobody on the floor remembers, unplug the network, and get the right answer back in seconds. It borrows credibility from a documented case in the same source material — Dell's Federal AI Anywhere writeup, where pairing a local GB10 model with the right task cut response time 47% and lifted accuracy 10% for an agency analyst. Different vertical, same shape of claim: on-device beats hand-searching.

Gaps to close before this goes further:

- No downtime-cost figure survived verification. The Frost & Sullivan set has company revenue and funding numbers, not a dollars-per-hour-of-stoppage baseline — and that number is what makes the "why this, why now" case land with judges. Needs an outside source.
- Dell's scenario is described as an "illustrative archetype," not a named customer, unlike the Federal AI Anywhere case which has a documented result attached. Worth checking whether a named manufacturing customer exists anywhere in Dell's material.
- No read on how much of a typical plant's manuals and fault history actually exists in machine-readable form versus paper — that's a build-risk question that directly sizes the RAG ingestion scope, not just a market question.
- No competitor doing this exact pattern (on-device, manuals-plus-fault-history, air-gapped) turned up in either source. Absence in a Factiva pull and twelve F&S reports isn't proof of absence — worth a fast check on whether Siemens, Rockwell, or PTC already ship something adjacent.
