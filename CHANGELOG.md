# Victoria Universalis IV — Version 2.0

**A full rebuild of the mod's core systems.** Religion and culture have been replaced from the ground up, the idea group system has been redesigned around Victoria 3's own economy and society, and four brand-new content layers add over 100 new events on top of it.

> ⚠️ **Start a new campaign.** Idea group identifiers were renamed and the old religion/culture systems were removed, so 2.0 is not save-compatible with 1.x.

---

## 🕌 Religion — completely rebuilt

The old missionary / holy site / religious aspect system is **gone**. Religion is now four layers that talk to each other:

**1. Religious Models (law-driven, not chosen).** Your Church and State law decides your model, and each one plays differently:

| Model | Character |
|---|---|
| **Confessional State** | Authority, conversion, Devout political strength — at the cost of migration and prejudice radicals |
| **Freedom of Conscience** | Migration and tolerance — weak conversion, heavy bureaucracy cost |
| **Total Separation** | The neutral model: fewest radicals, no conversion projects at all |
| **State Atheism** | Aggressive secularization: tech spread and education, but it fights the Devout |

Confessional states additionally get a small bonus package based on their faith family (Christian, Islamic, Jewish, Dharmic, Scholarly, Animist).

**2. Religious Settlement (0–100).** An equilibrium meter, not a bank. Each model has its own equilibrium target shaped by Devout approval, literacy, legitimacy, bureaucracy and turmoil — and the meter drifts toward it a few points a month. Above 75 you get a tier bonus; below 25 you bleed legitimacy and law enactment.

**3. Piety Reform (0–500).** A spendable currency. Every model has **8 permanent Religious Programs** (32 total) — Parish Schools, Interfaith Councils, Civil Code, Scientific Administration and so on. Each costs 25 Piety Reform and puts you on a 24-month implementation cooldown.

**4. Targeted Religious Projects.** Started from an individual state's panel: *Confessional Conversion*, *Freedom Outreach* or *Secularization Campaign*. Each runs 0–100 progress with real costs while active (bureaucracy, authority, radicals in the target state), and a Journal Entry tracks it — with incident events along the way (see below).

**Changing your Church and State law is now a real event.** A model change triggers a 36/48/60-month **Religious Settlement Crisis** and opens a *Transition Journey* Journal Entry with milestone decisions, closing in success, neutral or crisis depending on where your Settlement lands.

---

## 🏛️ National Identity — completely rebuilt

The old ±7 culture reform bar is **gone**. It mirrors religion, with its own identity:

- **Three Identity Models:** *Ethnic Nation* (assimilation and authority), *Civic Nation* (migration and education), *Composite State* (fewer minority radicals and more influence). Switching costs 200 Cultural Mandate and 60 months of backlash.
- **Cultural Mandate (0–500)** as the spendable resource and **National Cohesion (0–100)** as the equilibrium meter, driven by citizenship law fit, literacy, primary-culture share and plurality.
- **Five Cultural Projects:** countrywide *National Curriculum* and *Shared Symbols*, plus one model-specific state-targeted project each — *Ethnic Integration Campaign*, *Equal Citizenship Initiative*, *Constituent Compact*. Composite states permanently record recognized constituent cultures.
- Identity Model changes get their own **National Compact Transition Journey** with milestone decisions.

---

## 💡 Idea Groups — redesigned and rebalanced

**15 EU4-style groups have become 21 Victoria 3-native groups in three categories:**

- **Production (7):** Industrialist, Mercantile, Financial, Infrastructure, Extraction, Labour, **Agrarian** *(new)*
- **Society (7):** Academic, Bureaucratic, Parliamentary, Welfare, Diplomatic, Nationalist, Reformist
- **Military (7):** Offensive, Defensive, Naval, Professional Army, Mass Conscription, Colonial, War Economy

What changed mechanically:

- **Group slots are earned, not handed out by the calendar.** The old "+1 slot every ten years" is gone. Capacity now unlocks at 4 / 8 / 13 / 19 / 26 / 34 purchased idea levels, with Age gates on the last three slots. Max 7 groups per campaign.
- **Doctrine Implementation Strain:** every idea purchase locks further purchases for 24 months and reduces Insight income. Banking 1000 Insight no longer lets you buy a whole tree in one burst.
- **Technology gates:** Labour, Welfare, Nationalist, Reformist, Mass Conscription, Colonial and War Economy require the matching vanilla technology; Extraction VII needs Dynamite.
- **Mutually exclusive paths:** Agrarian / Extraction, Nationalist / Reformist, Professional Army / Mass Conscription.
- **Full balance pass:** completed-group totals normalized to roughly 20–30% in their lane; flat resource-output bonuses replaced with building throughput so they scale with production methods; bonuses that quietly hurt urbanization, wages or welfare were replaced with positive effects.
- **Doctrines now feed the other systems:** matching level V/VII ideas add Piety Reform and Cultural Mandate income and speed up Religious/Cultural Projects, and level IV ideas generate Era Momentum during their assigned Age.

---

## 🎖️ National Ideas — 12 new country profiles

National Idea progress now comes from **purchased idea levels** (3/6/9/12/15/18/21), so you don't need to complete a group to advance. New profiles added on top of the existing ten:

**Spain, Italy, Sweden/Scandinavia, India, Mexico, Brazil, Netherlands, Belgium, Persia, Egypt, Korea, Argentina** — each with 2 Traditions, 7 National Ideas and a National Bonus. Country formation correctly swaps your old profile for the new tag's.

---

## 🌍 Ages & Era Momentum — expanded

Three Ages (*Industry and Nations*, *Empire and Mass Society*, *Mass Politics and Total War*), each with 7 objectives that pay +1 Era Momentum per month while satisfied plus a one-time +50 on first completion.

- **13 Era Reward slots per Age** (9 shared + 4 country/culture-restricted, e.g. Ottoman law setbacks, Chinese innovation, British naval invasion, Japanese ship supply), with an escalating cost ladder of 200/300/400/500/600 that resets each Age.
- **Three Golden Age types** — Industrial, Cultural, Strategic — 15 years long, **one per campaign**, unlocked by securing five distinct objectives in an Age.

---

## ✨ New content layers (100+ new events)

**Idea Group Ambient Events (18 events, 54 options).** Your embraced doctrines now speak up on their own: dilemmas, opportunities and setbacks for Industrialist, Agrarian, Academic, Nationalist, Reformist and Professional Army. Higher idea levels unlock cheaper, better-fitting responses.

**Doctrine Journeys (3 chains).** Multi-year Journal Entry projects tied to what your country actually builds:

- *Standardizing the Factory System* (Industrialist) — manufacturing levels + healthy bureaucracy → +40 National Insight
- *Republic of Scholars* (Academic) — university levels + literacy growth → +15 Era Momentum
- *Reforming the General Staff* (Professional Army) — barracks + Professional Army law/General Staff tech → 36 months of training rate

**Era Crossroads (3 chains, 9 routes, 12 events).** One strategic Journey per Age, each with three routes anchored to objectives you've already secured: *Steam and the State*, *Empire and Mass Society*, *The Mobilized Society*. Completion pays +50 Era Momentum.

**Country Flavor Chains.** Tag-specific decision chains with year-long consequences:

- 🇹🇷 **The Language of Reform** (Ottomans) — civic lexicon vs. sacred continuity vs. administrative translation
- 🇯🇵 **Borrowed Methods, Native Authority** (Japan) — translation bureaus vs. directed borrowing vs. selective adoption
- 🇺🇸 **The Meaning of the Union** (USA) — citizenship compact vs. composite bargain vs. federal ambiguity

**Project Incident Events (36 events).** Religious and Cultural Projects are no longer silent progress bars. School disputes, registry fights, surname directives, constituent delegations, crises that can force you to cancel, and rare breakthroughs that only fire for well-run states with the right capstone doctrine.

---

## 🖥️ Interface

- **New topbar row.** Nine clickable chips — National Insight, Idea Groups, Piety Reform, Religious Settlement, Religious Project, Cultural Mandate, National Cohesion, Cultural Project, Era Momentum. Each opens the right panel tab, each tooltip carries the full breakdown.
- **Rebuilt Religion and National Identity pages.** One screen, no scrolling, no tabs: summary strip, models, programs, project — with live warnings whenever strain or backlash is blocking you.
- **National Doctrine section in the country panel.** A read-only doctrine readout for **any** country, yours or a rival's: resources, idea groups with purchase pips, National Idea slots, religious model and programs, identity model, Era standing and rewards.
- **Doctrine Ledger (new panel tab).** A sortable, filterable, paged table of every country's doctrine state — sort by prestige, Insight, ideas, groups, Settlement, Cohesion, Momentum or Era Rewards; filter to great powers, recognized states, your diplomatic neighborhood, or anyone with an idea group. Your own country is pinned as the baseline. Click a row to jump to that country.
- **State panel action cards** for starting, tracking and cancelling Targeted Religious and Cultural Projects, with tooltips that itemize exactly which requirement you're missing.
- **Clickable alerts.** Mod alerts now actually open the relevant mod panel instead of doing nothing.

---

## 🌐 Localization

**All 11 supported languages** — English, Turkish, French, German, Spanish, Polish, Russian, Simplified Chinese, Japanese, Korean, Brazilian Portuguese — received the complete 2.0 key set. 121 new localization files, and every existing file updated for the reworked mechanics and rebalanced modifier text.

---

## 🔧 Under the hood

- Retired systems fully removed (missionary values, holy sites, religious aspects, the old culture reform bar, the old information panel bar) — no more "variable used but never set" log spam on load.
- AI plays the new systems with the same rules as the player: it picks idea focuses, buys programs, chooses identity models and projects, targets its largest eligible states, and takes Era Rewards and Golden Ages.
- Save-compatible variable helpers and clamping across every resource, plus gameplay-neutral telemetry for tuning.
