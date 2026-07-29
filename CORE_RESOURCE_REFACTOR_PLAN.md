# Victoria Universalis IV — Core Resource Systems Refactor Plan

> Status: design and implementation handoff document  
> Scope: Idea Points, religion/atheism, culture/National Identity, Ages/Splendor  
> Implementation status: Phases 0-9 complete; the core resource refactor is implemented.
> Values in this document are initial balance targets unless
> explicitly marked as a locked decision.

## 0. Objective

The mod currently uses four parallel monthly currencies:

- `idea_point_pool`
- `piety_bar_point`
- `culture_reform_point`
- `ve_splender_points`

All four are granted by the same monthly workflow and are primarily spent when
a fixed threshold is reached. The refactor must replace this shared “wait for
mana, click a permanent bonus” structure with four systems that react to
Victoria 3's economy, institutions, laws, interest groups, population, turmoil,
legitimacy, diplomacy, and warfare.

The goal is not to remove every resource. The goal is to ensure that each
resource represents a different political or institutional process:

| System | New role | Resource behavior |
| --- | --- | --- |
| Ideas | National knowledge and implementation capacity | Accumulating resource with a soft cap |
| Religion | Relationship between state doctrine and society | Dynamic authority/harmony meter |
| Culture | Construction and management of national identity | Mandate resource plus cohesion state |
| Ages | Performance within the current historical era | Objective-based momentum reset each age |

## 1. Current-system diagnosis

### Shared monthly income

`common/scripted_effects/ve_monthly_effects.txt` grants all four resources every
month. `events/developer_events.txt` dispatches this from the monthly country
pulse.

### Idea Points

Current source: `monthly_idea_points` in
`common/script_values/ve_script_values.txt`.

- Player base: +13/month.
- Literacy contributes only +1 to +4.
- AI difficulty changes monthly income directly.
- Country economy, universities, innovation, legitimacy, bureaucracy, turmoil,
  and institutions have little or no effect.
- There is no meaningful stock soft cap.

### Piety

Current source: `monthly_piety_points`.

- Player base: +4/month.
- Theocracy, State Religion, religious law, and selected holy sites add small
  flat amounts.
- State Atheism currently generates piety.
- All religious aspects cost 125.
- Religious population, Devout approval, social conflict, legitimacy, and
  doctrinal consistency are not central to the calculation.

### Culture Reform Points

Current source: `monthly_culture_reform_point`.

- Player base: +7/month.
- Every country advances at almost the same speed.
- The current permanent axis is National Supremacy versus Intellectual Nation.
- “Intellectual Nation” is not a coherent cultural opposite to nationalism.
- Current rewards mix assimilation, conversion, technology, migration,
  bureaucracy, colonies, law enactment, and infamy without a clear identity.
- Demography, homelands, cultural acceptance, cultural movements, and turmoil
  do not drive the system strongly enough.

### Splendor

Current source: `monthly_splender_points`.

- Player base: +3/month.
- Each currently satisfied objective adds +2/month.
- Every reward costs 800.
- The free base produces 1260 Splendor during a 35-year age even if the country
  achieves nothing.
- Several rewards are locked to specific tags or cultures.
- Some objective descriptions and triggers disagree.
- Several objectives use absolute great-power thresholds, excluding small and
  medium countries.

## 2. Locked design principles

These decisions apply to every implementation phase.

1. The four resources must not use the same economic model.
2. Waiting without meaningful state development must not be the primary source
   of progress.
3. Country size alone must not determine resource generation. Prefer ratios,
   tiers, balance values, and relative achievements over absolute GDP,
   population, university count, or army size.
4. Strong actions must create a relevant cost: bureaucracy, authority,
   interest-group reaction, radicalism, temporary implementation strain,
   opportunity cost, or a competing policy path.
5. Negative conditions must slow or destabilize progress without creating an
   unrecoverable death spiral. Each system needs a minimum recovery route.
6. Hoarding must be controlled through a soft cap, dynamic equilibrium,
   escalating costs, or age reset.
7. AI difficulty must not grant different visible resource income. AI support,
   if needed, belongs in separate AI weighting or hidden difficulty modifiers.
8. Tooltips must display the real current income or pressure breakdown.
9. New identifiers must use the `ve_` prefix.
10. Static validation is sufficient for routine script work. User-run game
    testing is reserved for critical runtime-dependent transitions, dynamic
    panels, scope behavior, save migration, or engine-specific behavior.

## 3. Shared resource framework

The systems share technical infrastructure, not gameplay identity.

### Monthly update structure

Replace the single opaque resource grant with narrowly scoped effects:

- `ve_update_national_insight`
- `ve_update_religious_state`
- `ve_update_national_identity`
- `ve_update_era_momentum`

Each update should:

1. calculate the current monthly value or pressure through a script value;
2. apply minimum, maximum, soft-cap, or equilibrium behavior;
3. change only its own variables;
4. expose the same calculation to GUI tooltips;
5. avoid unbounded state/pop loops on the monthly country pulse.

Reusable calculations belong in:

- `common/script_values/`
- `common/scripted_triggers/`
- `common/scripted_effects/`

The monthly dispatcher should remain small.

### Income breakdown

Every resource tooltip should separate:

- base or minimum recovery;
- state capacity;
- laws and institutions;
- interest groups;
- demographic or economic conditions;
- temporary bonuses and penalties;
- cap/equilibrium adjustment;
- final monthly change.

### One-time changes

Journal entries, events, law enactment, war results, recognition, objective
completion, and major reforms may grant one-time resource changes. One-time
awards must use flags or variables so a monthly condition cannot repeatedly
grant the same completion reward.

### Difficulty

Remove `ve_easy`, `ve_medium`, and `ve_hard` branches from visible resource
income. AI strategy and spending weights should determine performance instead.

## 4. Ideas — National Insight

### Identity

Idea Points become **National Insight**: the state's ability to generate,
evaluate, and implement national doctrines.

The idea-group structure, tiered costs, ambitions, and completed-group national
idea progression from `IDEA_GROUP_BALANCE.md` remain the foundation.

### Resource model

- Accumulating stock.
- No negative balance.
- Initial hard target cap: approximately 900–1000.
- Soft-cap band begins around 700.
- Income is strongly reduced near the cap rather than silently discarded.

The cap must always be higher than the most expensive current idea (675).

### Monthly-income target

The complete game should normally allow four to five completed groups, with six
representing a strong long campaign. With the current 2800-point group cost,
the broad target is:

- weak or unstable country: 5–8/month;
- typical functioning country: 9–12/month;
- highly educated and capable country: 13–16/month.

These ranges are calibration targets, not final scripted values.

### Income factors

Positive:

- literacy tiers;
- education institution;
- university capacity relative to population;
- innovation production or effective innovation use;
- positive bureaucracy balance;
- government legitimacy;
- Intelligentsia or relevant professional-group approval;
- selected events, journals, and technological achievements.

Negative:

- bureaucracy deficit;
- default or severe debt crisis;
- high average turmoil;
- revolution or civil war;
- very low legitimacy;
- temporary implementation strain.

### Implementation strain

Ordinary early ideas should not produce excessive micromanagement. Temporary
strain should primarily be used for:

- capstones;
- ambitions;
- switching or cancelling a developed group;
- unusually transformative ideas.

Possible costs:

- temporary bureaucracy use;
- government wages;
- interest-group approval;
- reduced National Insight generation for 12–24 months.

### Country identity

Do not recreate separate ADM/DIP/MIL currencies. Instead, country conditions
may provide limited affinity discounts or one-time Insight rewards:

- industrial development supporting Production groups;
- education and institutions supporting Society groups;
- war experience and military organization supporting Military groups.

The player remains free to choose an unnatural strategy, but natural country
strengths provide a modest advantage.

### National ideas

Keep the completed-group model:

- incomplete groups give no `national_idea_pool` progress;
- each completed group grants three progress;
- thresholds remain 3/6/9/12/15/18/21 unless later balance data requires a
  change.

## 5. Religion — Three playable state models

Atheism must not disable a major game system. The religion panel changes its
identity according to the state's religious settlement.

### Model A: Confessional State

Applicable to State Religion and Theocracy-oriented states.

Resource: **Religious Authority**

Strengths:

- authority;
- conversion;
- loyalism and community cohesion;
- mobilization;
- religious charity or social support.

Costs:

- stronger Devout political power;
- resistance to conflicting reforms;
- minority radicalism or lower acceptance;
- doctrinal consistency requirements.

### Model B: Pluralist State

Applicable primarily to Freedom of Conscience and Total Separation.

Resource: **Religious Harmony**

Strengths:

- lower religious turmoil;
- migration and acceptance;
- interfaith stability;
- reduced radicalism from religious diversity.

Costs:

- lower conversion;
- less centralized religious authority;
- fewer direct authority/mobilization benefits;
- administrative cost for plural settlement.

### Model C: Atheist State

Applicable to State Atheism and an atheist state doctrine.

Resource: **Secular Legitimacy**

State Atheism transforms the religion panel into a **Secular State** panel.
Religious aspects are replaced by secular programs rather than simply removed.

Initial secular program set:

1. Scientific Administration
2. Civil Registry
3. Public Education Campaign
4. Secular Welfare
5. Civic Morality
6. Academic Freedom
7. Anti-Clerical Campaign

Typical strengths:

- education and qualifications;
- innovation or technology spread;
- civil administration;
- loyalism from legitimacy and living standards;
- reduced institutional power of the Devout.

Typical costs:

- bureaucracy and government wages;
- lower authority;
- religious-population radicalism;
- conservative interest-group opposition;
- difficult transition in a highly religious society.

### Dynamic authority/harmony model

Religion uses a dynamic state meter rather than an unlimited stockpile.

Initial design target:

- range: 0–100 or -100–100;
- monthly pressure toward a state-dependent equilibrium;
- adopting a doctrine or program can temporarily reduce the meter;
- high meter grants stability benefits;
- low meter produces relevant political or social problems.

Positive factors depend on the active model:

- Devout approval and state-religion population for Confessional states;
- low discrimination and low religious turmoil for Pluralist states;
- atheist/secular social support, education, and Intelligentsia approval for
  Atheist states.

Common negative factors:

- law and demographic mismatch;
- low legitimacy;
- turmoil among affected religious populations;
- doctrinally contradictory actions;
- loss of holy sites or failed state campaigns.

### Transition rules

Changing model starts a temporary settlement crisis. Severity depends on the
distance between the new law and society:

- state-religion or atheist population share;
- Devout and Intelligentsia clout/approval;
- literacy and education;
- discrimination and turmoil;
- existing doctrines/programs.

Old aspects must be removed, suspended, or converted through an explicit
transition effect. No stale modifier may survive the model change.

### Religious diversity

The first refactor establishes the three state models. Faith-family flavor may
then adjust doctrine availability and authority sources for:

- institutional Christian traditions;
- Islamic legal and scholarly traditions;
- Dharmic traditions;
- Buddhist and East Asian traditions;
- local/animist traditions;
- secular/atheist states.

Faith-family content must create different incentives without assigning an
objectively superior religion.

## 6. Culture — National Identity

The current Supremacy/Intellectual ladder is replaced rather than numerically
rebalanced.

### Core structure

The new system has three layers:

1. **Identity Model** — the state's long-term definition of the nation;
2. **National Cohesion** — current success of that model;
3. **Cultural Mandate** — capacity spent on projects and model changes.

### Identity Model A: Ethnic Nation

The nation is built around one or more primary national cultures.

Strengths:

- assimilation;
- authority;
- primary-culture loyalism;
- homeland mobilization;
- national cohesion in culturally aligned territory.

Costs:

- minority radicalism;
- reduced migration attraction;
- lower cultural acceptance;
- greater instability in diverse countries.

### Identity Model B: Civic Nation

The nation is built around citizenship, common law, education, and state
institutions.

Strengths:

- cultural acceptance;
- migration;
- loyalism from legitimacy and living standards;
- education and qualifications;
- lower minority turmoil.

Costs:

- higher bureaucracy requirement;
- reduced assimilation;
- lower authority;
- opposition from conservative interest groups.

### Identity Model C: Composite State

The state recognizes several constituent peoples while preserving a shared
imperial or federal framework.

Strengths:

- reduced homeland turmoil;
- constituent-culture management;
- regional autonomy;
- reduced secession pressure when legitimate;
- subject and imperial integration.

Costs:

- high bureaucracy/institution cost;
- slower assimilation;
- lower central authority;
- severe separatist risk when legitimacy and cohesion collapse.

### National Cohesion

Initial range: 0–100.

Cohesion is model-relative. Homogeneity is not universally good and diversity
is not universally bad.

Ethnic Nation values:

- primary culture and accepted-culture share;
- assimilation;
- homeland control;
- national legitimacy.

Civic Nation values:

- cultural acceptance;
- education;
- legitimacy;
- institutions;
- low discrimination and turmoil.

Composite State values:

- acceptance of constituent peoples;
- autonomy and administrative capacity;
- low homeland turmoil;
- legitimacy;
- successful subject/federal relations.

High cohesion provides modest identity-appropriate rewards. Low cohesion
creates project costs, radicalism, movement pressure, or secession risk rather
than a generic universal debuff.

### Cultural Mandate

Mandate is an accumulating but capped resource used for:

- beginning a cultural project;
- recognizing or integrating a constituent people;
- changing the Identity Model;
- responding to a cultural movement;
- accelerating or suppressing a national campaign.

Positive sources:

- legitimacy;
- positive bureaucracy balance;
- education;
- low turmoil;
- laws aligned with the selected model;
- support from relevant interest groups;
- successful cultural projects.

Negative sources:

- model/law contradiction;
- cultural movements;
- homeland turmoil;
- excessive discrimination;
- low legitimacy;
- recent identity reform backlash.

### Initial cultural project set

- Standardize National Language
- Establish National Curriculum
- Promote National Symbols
- Civic Service
- Recognize Regional Languages
- Grant Cultural Autonomy
- Integrate a Constituent People
- Imperial Citizenship
- Promote a Shared Identity
- Forced Assimilation Campaign
- Support a Cultural Revival
- Diaspora Engagement
- Pan-National Congress

Projects should be targeted and temporary processes, not immediate permanent
modifier purchases. Depending on the project they may target:

- the whole country;
- a selected culture;
- a selected state or homeland;
- a constituent subject.

### Vanilla cultural-acceptance integration

Current Victoria 3 includes:

- culture-specific `country_<culture>_cultural_acceptance_add` modifier types;
- `state_cultural_acceptance`;
- `country_average_cultural_acceptance`;
- cultural and pan-national political movements.

The refactor should use these native systems where practical instead of
building a parallel acceptance model. Exact dynamic-culture targeting must be
prototyped before committing to a GUI design; culture-specific generated
switches may be required if modifier names cannot be parameterized.

### Reform backlash

Major projects and Identity Model changes create temporary backlash:

- interest-group approval changes;
- reduced Mandate generation;
- radicals among affected cultures;
- temporary bureaucracy or authority cost;
- political-movement activity.

Backlash magnitude depends on demographics and laws, not a fixed universal
penalty.

### Existing cultural bureaucrats

The current “cultural missionary/bureaucrat” state-selection infrastructure may
be repurposed into project capacity or administrators. It should not remain as
a separate passive conversion counter if the new targeted-project system
supersedes it.

## 7. Ages — Era Momentum

### Age structure

Keep the current dates unless later compatibility work requires adjustment:

| Dates | New age |
| --- | --- |
| 1836–1870 | Age of Industry and Nations |
| 1871–1905 | Age of Empire and Mass Society |
| 1906–1936 | Age of Mass Politics and Total War |

### Momentum economy

Locked direction:

- no universal +3 monthly base;
- each currently satisfied objective grants +1/month;
- first completion of an objective grants an initial one-time target of +50;
- objective completion rewards are protected by per-age flags;
- losing an objective stops its monthly income but does not repeat the
  one-time reward;
- Momentum resets on age transition.

Initial escalating reward costs:

| Reward number within age | Target cost |
| --- | ---: |
| 1 | 200 |
| 2 | 300 |
| 3 | 400 |
| 4 | 500 |
| 5+ | 600 |

These values require mathematical calibration against expected objective
completion dates.

### Age 1 objectives — Industry and Nations

1. Industrial Takeoff — reduce peasant dependence or reach an industrialization
   threshold.
2. End of the Old Order — remove a major old-regime institution such as slavery
   or serfdom.
3. Functional State — maintain sufficient legitimacy and bureaucracy.
4. Educated Public — reach a literacy or education-institution threshold.
5. Integrated Market — establish strong market access and transport
   infrastructure.
6. National Awakening — achieve national consolidation, formation, or strong
   National Cohesion.
7. Diplomatic Recognition — improve rank, gain recognition, or establish
   regional diplomatic relevance.

### Age 2 objectives — Empire and Mass Society

1. Industrial Power — develop a major manufacturing sector or lead a relevant
   industrial good.
2. Mass Education — reach a literacy or education-institution threshold.
3. Empire or Sovereignty — build an overseas/subject sphere or achieve
   independence and recognition against imperial pressure.
4. Global Commerce — establish trade, convoy, port, or market reach.
5. Nation Building — achieve high National Cohesion or complete a major
   integration project.
6. The Social Question — develop health, workplace safety, or welfare
   institutions.
7. Modern Armed Forces — field modern production methods and logistics rather
   than merely a large unit count.

### Age 3 objectives — Mass Politics and Total War

1. Mass Politics — establish broad political participation or an alternative
   stable mass-mobilization model.
2. Social State — maintain several developed social institutions.
3. Electrified Economy — produce and use electricity at meaningful scale.
4. Oil and Engines — develop oil, engines, automobiles, or modern logistics.
5. Modern Military — use advanced infantry, artillery, and support production
   methods.
6. Total War Capacity — maintain military industry and mobilization capacity.
7. World Influence — become a Great Power/power-bloc leader or achieve a major
   success against one.

Objectives should support alternatives so a small independent country, a
peaceful industrial country, and an imperial great power do not all receive the
same checklist.

### Reward structure

Replace eleven mixed and tag-locked rewards with nine condition-based rewards
per age:

- three State & Society;
- three Economy & Technology;
- three World & Military.

No reward should be locked to a specific country tag. Conditions may require a
relevant playstyle, such as ports, colonial law, institutions, conscription, or
industrial capacity.

#### Age 1 reward concepts

State & Society:

- Centralized Administration
- Public Schooling
- Constitutional Practice

Economy & Technology:

- Sound Credit
- Industrial Standards
- Railway Coordination

World & Military:

- Professional Diplomacy
- Maritime Logistics
- Army Reform

#### Age 2 reward concepts

State & Society:

- Mass Education
- Public Health
- Administrative Reach

Economy & Technology:

- Resource Surveying
- Corporate Organization
- Global Commerce

World & Military:

- Colonial Administration
- Diplomatic Networks
- National Mobilization

#### Age 3 reward concepts

State & Society:

- Welfare Administration
- Mass Politics
- Scientific State

Economy & Technology:

- Electrified Infrastructure
- Mass Production
- Strategic Industry

World & Military:

- Home Front
- Mechanized Logistics
- International Congress

Exact modifiers must be selected from current vanilla
`common/modifier_type_definitions/` and checked against existing idea groups to
avoid creating mandatory stacked combinations.

### Golden Age

The current all-purpose military/economic Golden Age modifier is replaced.

After satisfying at least four distinct objectives, the country may activate
one Golden Age type:

- Industrial Zenith
- Cultural Zenith
- Strategic Zenith

Initial duration target: 10–15 years. It should be available once per game
unless later design chooses once per age. Each type has a focused identity and
must not provide universal offense, navy, manufacturing, and mining bonuses
simultaneously.

## 8. Reward and penalty philosophy

Rewards should:

- reinforce the strategy that generated them;
- solve a focused problem;
- avoid replacing core Victoria 3 systems;
- remain useful without becoming mandatory;
- use scalable multipliers where appropriate.

Penalties should:

- follow logically from the player's choice;
- create political or administrative consequences;
- be visible before confirmation;
- be recoverable;
- avoid arbitrary permanent punishment.

Preferred costs:

- bureaucracy;
- authority;
- government wages;
- interest-group approval;
- cultural/religious radicalism;
- temporary implementation strain;
- loss of an incompatible benefit.

Avoid:

- unexplained flat debuffs;
- unavoidable negative spirals;
- punishing small countries solely for size;
- giving every route the same modifiers with different names.

## 9. AI design

AI must use the same visible resource rules as the player.

### Ideas

- prioritize affordable active groups;
- prefer groups matching economy, military position, and diplomacy;
- respect exclusive paths and age gates;
- avoid hoarding above the soft cap.

### Religion

- choose a state model based on laws, religious demography, Devout and
  Intelligentsia strength, and current turmoil;
- avoid State Atheism in a highly religious unstable country without a strong
  political reason;
- choose doctrines/programs appropriate to the active model.

### Culture

- choose Identity Model from cultural diversity, homelands, laws, subjects,
  migration, and acceptance;
- react to low Cohesion and cultural movements;
- avoid projects that contradict the current model unless intentionally
  transitioning.

### Ages

- select rewards matching actual country conditions;
- avoid colonial/naval rewards when irrelevant;
- spend Momentum before age reset;
- choose a Golden Age at a strategically useful time.

## 10. UI direction

### Topbar

The topbar must not show four unexplained currencies with static tooltips.

- National Insight remains a stock value.
- Religion shows the active state-model name and current meter.
- Culture shows Mandate and Cohesion.
- Ages show current Momentum and objective income.

If space becomes excessive, religion/culture secondary values should appear in
their panels rather than adding more permanent topbar counters.

### Idea panel

- display current Insight income breakdown and soft-cap status;
- show implementation strain before purchase;
- preserve tier cost and completed-group national progress.

### Religion panel

- dynamically present Confessional, Pluralist, or Secular State content;
- clearly preview transition crisis and doctrine/program tradeoffs;
- remove or suspend incompatible old modifiers reliably.

### National Identity panel

- show selected model;
- show Cohesion and its causes;
- show Cultural Mandate income;
- show significant cultures/homelands where technically feasible;
- present active projects, targets, duration, progress, and backlash.

### Age panel

- show first-completion reward and active monthly Momentum for each objective;
- show escalating next-reward cost;
- group rewards into three branches;
- remove country-tag-only buttons;
- show Golden Age availability and alternatives.

## 11. Save compatibility and migration

This refactor changes the meaning of core variables and removes/replaces
permanent modifiers. Full compatibility with existing saves is not a design
requirement.

Recommended policy:

- require a new game for the complete refactor;
- add defensive initialization for released and civil-war countries;
- remove stale old modifiers during initialization;
- do not attempt to infer a complete National Identity or religious settlement
  from every old save unless a small deterministic conversion is safe.

If partial migration is retained:

- old idea points may be clamped into the new Insight cap;
- old piety must not transfer directly into Secular Legitimacy;
- old culture ladder modifiers must be removed before selecting a new model;
- Splendor should reset to the current age's clean state.

## 12. Implementation phases

### Phase 0 — Audit and dependency map

- inventory every resource read/write;
- inventory alerts, GUI displays, scripted values, effects, AI, events, and
  localization;
- inventory old permanent modifiers and cancellation paths;
- confirm all required vanilla triggers/effects/modifier definitions;
- mark save-incompatible identifiers and variables.

Deliverable: complete dependency table with no implementation behavior change.

### Phase 1 — Shared framework

- split monthly update effects;
- expose stable stock and monthly-change script values to update effects and
  GUI;
- implement cap/equilibrium behavior inside the relevant system's vertical
  migration rather than imposing one shared resource rule;
- implement tooltip-facing calculation values;
- remove visible-resource difficulty branches;
- preserve old behavior temporarily behind the new interfaces if necessary.

Deliverable: shared infrastructure with unchanged or deliberately bridged
gameplay.

### Phase 2 — National Insight

- implement new income formula;
- implement soft cap;
- integrate relevant temporary strain;
- update tooltips, alert, AI spending, and initialization;
- preserve completed-group national idea progression.

Deliverable: first fully migrated resource and reference pattern.

### Phase 3 — Era Momentum

- rename/reframe ages;
- rebuild objective triggers and localization;
- add one-time completion flags and monthly active income;
- implement escalating reward costs;
- replace tag-locked rewards with branch rewards;
- replace Golden Age.

Deliverable: objective-driven age system with no passive free Splendor.

### Phase 4 — Religious state models

- implement Confessional, Pluralist, and Atheist model detection;
- implement dynamic meter calculation;
- refactor religious aspects into model-appropriate doctrines;
- create Secular State programs;
- implement settlement transitions and crises;
- update AI, panel, alerts, and localization.

Deliverable: State Atheism and pluralism as full playable alternatives.

### Phase 5 — National Identity foundation

- remove the old Supremacy/Intellectual ladder;
- implement Identity Model variables and modifiers;
- implement Cohesion calculation;
- implement Cultural Mandate;
- update initialization and model transition effects.

Deliverable: three functional identity models.

### Phase 6 — Cultural projects and acceptance

- prototype dynamic culture/state targeting;
- integrate vanilla cultural acceptance and political movements;
- implement initial project set;
- repurpose or remove cultural bureaucrats;
- add backlash, duration, completion, and cancellation flows;
- implement AI project selection.

Deliverable: country-specific cultural gameplay driven by demographics.

### Phase 7 — Integration and balance pass

- inspect cross-system modifier stacking;
- prevent one law/build from dominating several resource systems;
- calibrate expected completion rates;
- verify released/civil-war-country initialization;
- clean old identifiers, dead scripts, alerts, and localization;
- update design documentation with final values.

## 13. Verification strategy

Routine verification:

- identifier/reference search;
- brace and GUI nesting checks;
- localization-key checks;
- modifier-definition checks against the read-only vanilla installation;
- cost/income mathematical simulations;
- old-variable and stale-modifier searches;
- AI/player rule parity checks.

Critical runtime verification is required only for:

- dynamic religion-panel transformation;
- religious settlement transitions and modifier cleanup;
- National Identity model transitions, panel bindings, and legacy-save cleanup;
- dynamic culture/state project targeting;
- age objective first-completion flags;
- age transition reset;
- on-action dispatch and released/civil-war initialization;
- any save migration retained in scope.

When logs are relevant, inspect the read-only diagnostic directory:

`C:\Users\prost\OneDrive\Documents\Paradox Interactive\Victoria 3\logs`

## 14. Main mod files currently involved

Resource generation and dispatch:

- `common/script_values/ve_script_values.txt`
- `common/scripted_effects/ve_monthly_effects.txt`
- `common/on_actions/ve_code_on_actions.txt`
- `events/developer_events.txt`
- `common/scripted_effects/ve_set.txt`

Ideas:

- `common/scripted_effects/ve_idea_effects.txt`
- `common/scripted_effects/ve_scripted_effects.txt`
- `common/scripted_triggers/ve_scripted_triggers.txt`
- `common/scripted_guis/ve_idea.txt`
- `common/scripted_guis/ve_national_ideas.txt`
- `gui/ve_panel_ideas.gui`
- `common/static_modifiers/ve_group_ideas.txt`

Religion:

- `common/scripted_effects/ve_religion_effects.txt`
- `common/scripted_guis/ve_religion.txt`
- `gui/ve_panel_religion.gui`
- `common/static_modifiers/ve_religion_aspects.txt`
- `common/static_modifiers/ve_holy_sites.txt`
- `common/customizable_localization/ve_religion_aspect_cl.txt`

Culture:

- `common/scripted_guis/ve_culture.txt`
- `gui/ve_panel_culture.gui`
- `common/static_modifiers/ve_culture.txt`
- cultural missionary effects, triggers, and script values

Ages:

- `common/scripted_guis/ve_ages.txt`
- `gui/ve_panel_age_bonusses.gui`
- `common/static_modifiers/ve_age.txt`
- `events/ve_age_events.txt`
- `events/developer_events.txt`

Shared:

- `common/scripted_effects/ve_ai_effects.txt`
- `common/alert_types/ve_alert_types.txt`
- `gui/topbar.gui`
- `localization/english/ve_*_l_english.yml`

Vanilla reference sources:

- `common/modifier_type_definitions/`
- cultural and pan-national political movements;
- laws and institutions;
- scripted triggers/effects using cultural acceptance;
- comparable vanilla GUI panels and scripted GUIs.

## 15. Acceptance criteria

The refactor is complete when:

1. no resource is primarily a universal fixed monthly allowance;
2. each resource has a distinct gameplay model;
3. State Atheism retains a full, enjoyable mechanic;
4. Confessional, Pluralist, and Atheist states have different strengths and
   costs;
5. the old culture ladder is fully replaced by National Identity;
6. Ethnic Nation, Civic Nation, and Composite State are all viable;
7. demographics, acceptance, homelands, laws, and turmoil materially affect
   cultural gameplay;
8. Splendor is earned through age performance rather than free base income;
9. age objectives support multiple country archetypes;
10. age rewards have no country-tag locks;
11. AI follows the same visible resource rules;
12. UI tooltips expose real calculations and tradeoffs;
13. stale variables/modifiers from removed systems cannot survive
    initialization or transitions;
14. final modifier values are validated against current vanilla definitions and
    cross-system stacking.

## 16. Open calibration decisions

These should be decided during implementation with script math and content
review, not guessed in advance:

- exact National Insight formula and cap thresholds;
- whether religion uses 0–100 or -100–100;
- exact doctrine/program count per religious model;
- whether Golden Age is once per game or once per age;
- exact Momentum first-completion award and escalating costs;
- number of simultaneously active cultural projects;
- how many significant cultures the National Identity panel can target safely;
- whether Identity Model changes require a cooldown in addition to backlash;
- final names and localization tone for resources and models.

## 17. Phase 0 audit result

Phase 0 was completed before changing resource behavior. The existing storage
variables remain in place during the bridge so save migration and stale-state
cleanup can be implemented deliberately rather than through a mass rename.

### Dependency map

| Target system | Current storage | Monthly calculation | Main spenders and writers | Player-facing dependencies |
| --- | --- | --- | --- | --- |
| National Insight | `idea_point_pool` | `monthly_idea_points` | idea purchase effects and scripted GUIs; developer controls; released-country inheritance | idea panel, topbar, idea alert, AI idea selection |
| Religious State | `piety_bar_point` | `monthly_piety_points` | religion aspect effects and scripted GUIs; developer controls | religion panel, topbar, piety alert, aspect customizable localization, AI religion selection |
| National Identity | `culture_reform_point` | `monthly_culture_reform_point` | fourteen culture reform GUIs; AI reform selection; developer controls; released-country inheritance | culture panel, topbar, culture alert, cultural missionary system |
| Era Momentum | `ve_splender_points` | `monthly_splender_points` | age reward GUIs; `splendor_cost`; AI age selection; developer controls; age-transition resets | age panel, topbar, age alert, objective display |

All four resources are currently granted by `ve_monthly_points`, called from
hidden monthly event `dev.4`. The same event also performs initialization,
idea-slot updates, holy-site updates, law-change synchronization, atheism
cleanup, missionary cleanup, and all AI spending. Resource generation must
remain cheap because it shares this country-monthly pulse.

### Auxiliary state that must migrate with the resources

- Ideas: group-level variables, idea selection variables,
  `national_idea_pool`, idea slot variables, and idea cancellation paths.
- Religion: permanent passive modifiers, eight aspect slots, aspect selection
  variables, holy-site modifiers, missionary counts, and atheism cleanup.
- Culture: `culture_reform_value`, `selected_reform_value`,
  `stop_getting_reform_point`, fourteen ladder modifiers and flags, cultural
  missionary counts, selected states, and AI reform choices.
- Ages: three global age flags, transition-trigger globals,
  `ve_triggered_objectives`, objective state, all age reward modifiers, and
  Golden Age state.

### Lifecycle and migration hazards

1. Released and civil-war countries currently inherit only Idea Points and
   Culture Reform Points from two rank-one-country global accumulators in
   `dev.8`. This is brittle and must be replaced with explicit initialization
   based on the new country's current conditions.
2. Age transitions in `dev.5` and `dev.6` reset Splendor for every country and
   remove every modifier from the previous age. The Momentum migration must
   retain this cleanup guarantee while also clearing completion flags and
   escalating-cost state.
3. State Atheism currently receives piety income, uses atheist versions of the
   same aspect slots, and receives missionary capacity. The new Atheist State
   cannot reuse these semantics accidentally.
4. `ve_law_change_effects` couples religion law to missionaries and
   citizenship law to cultural missionaries. Identity-model and religious-model
   transitions must replace or explicitly preserve those side effects.
5. Culture reform purchases duplicate their point cost and ladder mutation
   across player scripted GUIs and AI effects. The replacement needs one shared
   purchase/project effect to prevent rule drift.
6. Religion aspect eligibility text repeats piety checks throughout
   customizable localization. Meter and model checks need centralized scripted
   triggers before the panel is rewritten.
7. Existing alerts test fixed costs (125, 750, and 800). They must move with
   each system and must not remain active against compatibility variables.

### Vanilla support confirmed during the audit

- current Victoria 3 exposes country/state cultural-acceptance triggers,
  including state and country-average acceptance;
- per-culture country acceptance modifier types exist in the current vanilla
  modifier definitions;
- laws, institutions, interest-group state, legitimacy, literacy, bureaucracy,
  turmoil, and economic balance can therefore supply native inputs instead of
  parallel EU4-style mana rules;
- dynamic culture targeting and runtime application of per-culture acceptance
  remain a critical prototype item for Phase 6 because the target-dependent
  modifier wiring is engine-sensitive.

### Phase 1 bridge decision

The monthly dispatcher now delegates to four stable entry points:

- `ve_update_national_insight`;
- `ve_update_religious_state`;
- `ve_update_national_identity`;
- `ve_update_era_momentum`.

During the compatibility bridge these effects still use the legacy variables
and formulas through stable `ve_*_value` and `ve_monthly_*` script values, so
the structural change does not alter balance. Difficulty branches remain only
inside those legacy formulas and will be removed when each visible resource is
migrated; removing them before a replacement formula exists would create an
arbitrary temporary balance change. Each later phase will replace exactly one
entry point, then migrate its GUI, alert, AI, initialization, and cleanup as a
single vertical slice.

## 18. Phase 2 implementation result — National Insight

National Insight is the first fully migrated resource. It intentionally retains
`idea_point_pool` as its save-compatible storage variable while all active
calculations and affordability checks use `ve_`-prefixed interfaces.

### Monthly model

The pre-cap monthly value is built from:

- base recovery: +6;
- literacy: +1 to +4;
- education institution: +0 to +3;
- university capacity in population-scaled bands: +0 to +2;
- healthy or overworked administration: +1 or -2;
- government legitimacy: -2 to +2;
- Intelligentsia approval: -1 to +1;
- loans, country turmoil, and active implementation strain: 0 to -5.

The result is clamped to 2-18 before stock pressure. Income is multiplied by
0.5 from 750 stock, by 0.25 from 900 stock, and by 0 at 1000. All recurring and
known one-time changes use a shared hard clamp of 0-1000.

### Purchase strain

Buying any idea applies `ve_national_insight_implementation_strain` for 24
months. It costs 25 Bureaucracy and 25 Authority and reduces Insight generation
by 2 per month while active. The strain now also blocks another group-idea
purchase for its full duration, so rapid purchases cannot compress several
doctrines into one implementation window.

### Migration changes

- player and AI use the same visible monthly formula;
- idea affordability checks use `ve_national_insight_value`;
- the topbar and idea panel display the calculated monthly breakdown;
- the obsolete rank-one-country global Idea Point inheritance was removed;
- released and civil-war countries begin from their own initialized stock and
  immediately generate Insight from their own conditions;
- the obsolete literacy-only custom localization and legacy monthly Idea Point
  formula were removed;
- the Innovative idea event now awards the actual resource variable rather than
  accidentally creating a variable named after the old script value.

## 19. Phase 3 implementation result — Era Momentum

Splendor has been replaced in player-facing text and active calculations by
Era Momentum. The save-compatible `ve_splender_points` variable remains the
underlying stock while all live logic uses the new centralized values,
triggers, effects, and scripted GUIs.

### Objective-driven income

- the universal +3 monthly allowance and AI difficulty income are no longer
  used by the live monthly update;
- each currently satisfied objective grants +1 Era Momentum per month;
- each of the seven objectives grants +50 once on its first completion in an
  age;
- losing an objective removes its monthly income but does not erase completion
  or permit the +50 award to repeat;
- each age transition resets stock, completed-objective count, escalating cost
  state, and the preceding age's completion flags.

The three age sets now focus on Industry and Nations, Empire and Mass Society,
and Mass Politics and Total War. Scale-sensitive alternatives allow both large
powers and successfully modernized small countries to participate.

### Rewards and Golden Ages

- every age offers nine tag-neutral rewards across state/society,
  economy/technology, and world/military themes;
- costs escalate per age from 200 to 300, 400, 500, and then 600 for every
  later purchase;
- AI uses the same affordability trigger, escalating cost, and purchase effect
  as the player;
- four distinct completed objectives unlock one once-per-game Golden Age
  choice: Industrial, Cultural, or Strategic;
- each Golden Age lasts 15 years and has a focused modifier package.

The age panel now exposes the actual current income, completed-objective count,
and next reward cost. Legacy reward slots 10 and 11 remain defined only for
old-save cleanup and are hidden from the live UI.

## 20. Phase 4 implementation result — Religious State

Piety has been replaced by a 0–100 state-of-society meter. The save-compatible
`piety_bar_point` variable remains the storage layer, while laws select one of
three playable models:

- State Religion uses **Religious Authority**;
- Freedom of Conscience and Total Separation use **Religious Harmony**;
- State Atheism or an atheist state religion uses **Secular Legitimacy**.

### Equilibrium model

The meter moves by 20 percent of the distance toward its current equilibrium,
rounded and capped at five points per month. Equilibrium responds to:

- model-specific support from the Devout, Intelligentsia, literacy, and the
  selected Church and State law;
- government legitimacy and administrative capacity;
- country turmoil;
- an active settlement transition or program implementation strain.

The target is clamped to 15–85, leaving a recovery route during crises while
preventing passive permanent maximum strength. Values at 75 or above grant a
model-specific established-settlement benefit; values at 25 or below impose a
shared political crisis.

### Doctrines and programs

Each model has eight permanent choices with model-specific rewards. Adoption
requires at least 50 meter strength, consumes 25, and creates 24 months of
administrative and authority strain. The three sets emphasize:

- Confessional State: authority, conversion, community institutions,
  mobilization, and Devout power;
- Pluralist State: legitimacy, migration, education, qualifications,
  administration, and reduced centralized conversion;
- Secular State: bureaucracy, civil registration, public education, welfare,
  innovation, civic legitimacy, and reduced Devout power.

Player and AI actions use the same affordability and purchase effects.
Confessional states also receive a deliberately smaller faith-family package
for Christian, Islamic, Jewish, Dharmic, Buddhist/East Asian, or local sacred
traditions. This preserves religious texture without making faith choice more
important than the state's actual political settlement.

### Transitions and legacy migration

The monthly lifecycle detects a changed religious model. A transition removes
all old religion aspects, all programs from the previous model, passive
settlement modifiers, and holy-site benefits that are no longer applicable.
It resets the meter to 35 and applies a 36–60 month settlement crisis; adopting
State Atheism in a low-literacy or strongly clerical society receives the
longest transition.

State Atheism now has no missionaries. Pluralist states retain missionaries
only under Freedom of Conscience, while Total Separation disables them. Holy
sites are a Confessional State subsystem and are hidden and mechanically
cleared under Pluralist and Secular settlements.

## 21. Phase 5 implementation result — National Identity

The permanent National Supremacy versus Intellectual Nation ladder has been
removed from live gameplay. `culture_reform_point` remains the save-compatible
storage variable but is now presented and calculated as **Cultural Mandate**.
Countries select one of three viable political definitions of the nation:

- **Ethnic Nation** emphasizes assimilation, authority, and mobilization, while
  reducing migration attraction and making open prejudice more destabilizing;
- **Civic Nation** emphasizes migration, education, qualifications, and shared
  citizenship, while consuming administration and reducing authority and
  centralized assimilation;
- **Composite State** emphasizes negotiated coexistence, lower discrimination
  pressure, legitimacy, and diplomatic influence, while requiring the most
  administration and limiting assimilation.

### Cultural Mandate

Mandate has a hard cap of 500 and a soft-cap band beginning at 400. Monthly
income has a recovery base of 2 and responds to legitimacy, bureaucracy,
literacy, turmoil, transition backlash, and alignment between the selected
Identity Model and Citizenship law. The pre-cap result is clamped to 1–8;
income is halved from 400 and stops at 500.

Changing Identity Model costs 200 Mandate, resets National Cohesion to 35, and
applies 60 months of Identity Transition Backlash. The backlash consumes
Bureaucracy and Authority, reduces law-enactment success, slows Mandate
generation, and prevents another model change until it expires.

### National Cohesion

National Cohesion is a 0–100 dynamic meter. It moves by 20 percent of the
distance toward equilibrium each month, rounded and capped at five points.
The equilibrium is clamped to 15–85 and responds to legitimacy,
administrative capacity, turmoil, transition backlash, model-law alignment,
and model-specific conditions such as literacy.

At 75 or more, each Identity Model grants a distinct cohesion reward. At 25 or
less, all models suffer reduced legitimacy and law-enactment success. This
makes an identity choice strongest when supported by the country's laws and
institutions instead of functioning as a free permanent bonus package.

### Migration and temporary bridge

Initialization selects a deterministic model from current Citizenship law,
sets Cohesion safely, clamps inherited Mandate, and removes all fourteen old
ladder modifiers and their state variables. Player and AI model changes share
the same triggers, costs, cooldown, and effects. The alert, developer controls,
topbar, and National Identity panel now use the new model.

The cultural-bureaucrat/diffusion system remained as a temporary compatibility
bridge until Phase 6 validated dynamic state and culture targeting.

## 22. Phase 6 implementation result — Cultural Projects and Acceptance

The old pool of cultural bureaucrats and its automatic six-month assimilation
pulse have been removed from live gameplay. Cultural Mandate now funds one
visible Cultural Project at a time. All projects progress from 0 to 100 through
the same monthly calculation, which responds to administration, legitimacy,
literacy, National Cohesion, cultural-movement pressure, and—in targeted
projects—the target state's turmoil. Monthly progress is clamped to 1–7.

### Countrywide projects

- **National Curriculum** costs 100 Mandate and creates a ten-year education
  and qualifications program after completion.
- **Shared Symbols** costs 75 Mandate and creates an eight-year authority and
  loyalist-generation program after completion.

Both projects return a small amount of Mandate and Cohesion when completed,
making completion rewarding without refunding the initial investment.

### Identity-specific targeted projects

Targeted projects are started from an owned state's panel. The largest
eligible non-primary culture comprising at least five percent of that state
becomes the explicit project target:

- **Ethnic Integration Campaign** costs 125 Mandate, creates political
  resistance, converts five percent of the targeted culture in the selected
  state into a primary culture on completion, and leaves a ten-year
  assimilation program.
- **Equal Citizenship Initiative** costs 100 Mandate and grants the target
  culture +15 Acceptance for ten years, local loyalists, and a ten-year
  qualifications and migration program.
- **Constituent Compact** costs 150 Mandate, requires at least 40 Cohesion, and
  permanently grants the target culture +15 Acceptance. The culture is then
  recorded as a recognized constituent and cannot be selected for another
  compact.

Changing Identity Model safely cancels the current project before transition.
Voluntary cancellation does not refund Mandate, removes five Cohesion, and
creates a two-year administrative and political backlash.

### Interface, AI, and migration

The National Identity panel now shows exact project costs, durations,
completion results, active target culture and state, current progress, and the
full monthly progress breakdown. The state-panel action and culture alert have
been repurposed for targeted projects. AI countries use the same costs,
eligibility rules, target selection, progress, and outcomes as players.

Initialization clears old cultural-bureaucrat counters and state assignments.
The legacy citizenship-law synchronization no longer recreates them, and the
old half-yearly cultural conversion code is no longer dispatched. Dynamic
stored state/culture scopes and the native culture-acceptance effect are used
instead of parallel culture variables.

## 23. Phase 7 implementation result — Integration and balance

The final pass audited all four resources together instead of balancing each
panel in isolation. Modifier types were checked against the current read-only
vanilla definitions, duplicate live identifiers were removed, and the
recurring lifecycle was reviewed for player, AI, released-country, civil-war,
and old-save initialization.

### Final pacing targets

- one complete Idea Group costs 2,800 National Insight. Before purchase strain
  and soft-cap pressure, sustained monthly income of 8–16 completes a group in
  roughly 15–29 years; every purchase starts a 24-month implementation window
  during which another group idea cannot be adopted;
- Era Momentum grants one point per currently satisfied objective each month
  and 50 once per distinct objective. In a 35-year age, maintaining roughly
  four objectives supports about five of the nine rewards, while six objectives
  supports about six;
- Religious-State programs remain 25-point permanent choices, but Program
  Implementation Strain now prevents another adoption for 24 months. Acquiring
  all eight therefore takes at least 14 years instead of being compressed into
  a few high-equilibrium years;
- Cultural Projects require 100 total progress. At the normal 4–6 monthly
  range they last about 17–25 months; severe instability can extend a project
  toward the 100-month floor, while the absolute best case remains 15 months;
- 100 Cultural Mandate takes about 13–25 months at the intended 4–8 income
  range, before the 400-point soft cap and the administrative cost of an active
  project.

### Cross-system specialization

Generic state capacity still matters, but a single high-literacy or
high-bureaucracy build no longer maximizes every cultural route:

- Civic Nation receives the strongest literacy contribution;
- Ethnic Nation receives its social contribution from primary-culture
  demographic concentration;
- Composite State receives it from a genuinely plural population;
- Civic Cohesion falls when a non-primary culture above ten percent of the
  population remains at very low Acceptance;
- all models still react to cultural movements, turmoil, legitimacy, and their
  Citizenship-law alignment.

Potential innovation stacking was also reduced. Established Secular States now
receive technology spread rather than another flat innovation source, and
Academic Freedom grants +3 rather than +5 weekly innovation. This preserves a
strong scientific route without allowing the religious model, an Idea Group,
and an Era reward to create excessive flat innovation together.

### Lifecycle and cleanup

- Era Momentum now has an idempotent monthly initializer. Old saves that
  already possess the mod's main initialization flag but lack Phase 3 counters
  reconstruct reward ownership and Golden Age state safely;
- released and civil-war countries initialize the four storage resources and
  then pass through the same model/project/objective initialization as every
  other country on their first monthly pulse;
- the former cultural-missionary topbar element, alert terminology, state
  action identifiers, cultural counters, conversion dispatch, and live
  diffusion hooks were removed or renamed to Cultural Project terminology;
- Nationalist Idea V now affects only Missionary Conversion Power, while
  Nationalist Idea VII is the sole source of its advertised +2 missionary
  capacity. Acquiring or cancelling Idea VII immediately resynchronizes
  capacity from the current Church and State law without double-counting;
- six duplicate definitions of the missionary annex-cleanup effect were
  consolidated into one deterministic definition;
- obsolete compatibility bindings were subsequently removed in Phase 9; the
  live resource flow no longer depends on the superseded aspect or cultural
  missionary architecture.

### Final verification

The completed implementation passed brace and GUI-nesting checks, unique
identifier checks by content category, English localization reference and
duplicate-key checks, modifier-definition checks against the current vanilla
installation, stale active-reference searches, and whitespace validation.
Player and AI actions share the same affordability triggers and mutation
effects for Ideas, Religious Programs, Identity changes, Cultural Projects,
Era rewards, and Golden Ages.

## 24. Phase 8 implementation result — UI and tooltip clarity

The four resource panels now expose the values needed to make decisions
without consulting source files or guessing hidden thresholds.

- National Insight displays its live income breakdown and correct 1,000-point
  scale. Idea purchase buttons list all seven tier costs, the 24-month
  implementation strain, and the no-refund rule;
- Religious Settlement displays its exact equilibrium components, monthly
  convergence rule, and the effects of the 25/75 thresholds. Every Religious
  Program tooltip changes with the active settlement and states its permanent
  modifier before showing affordability and cooldown requirements;
- National Identity displays exact Mandate and Cohesion inputs. Cultural
  Projects expose current and remaining progress, monthly components, target,
  administrative burden, cancellation consequences, and completion outcome;
- Era Momentum displays satisfied and completed objectives, monthly income,
  rewards purchased, the full escalating cost ladder, and the age-reset rule.
  Each Golden Age choice now states its distinct 15-year effects.

Incorrect vanilla `BUILDING_PROGRESS_TOOLTIP` bindings were removed from the
custom Insight and Religious Settlement bars. All custom resource bars now
route to their own mechanical explanation, and the Insight bar uses its actual
1,000-point cap.

The UI pass passed script/GUI brace checks, English localization reference and
duplicate-key checks, scripted-value reference checks, customizable
localization reference checks, and whitespace validation.

## 25. Phase 9 implementation result — major-patch support policy

The refactor is now a major-patch baseline rather than an old-save migration.
Only English localization is maintained for new and changed player-facing text.
Non-English localization files are intentionally not synchronized.

The active initialization paths no longer scan for, remove, or reconstruct
superseded Cultural Missionary, religion-aspect, or culture-reform state. New
campaigns therefore enter the current resource systems directly.

The obsolete religion-aspect GUI, effects, customizable localization, and
static-modifier files were removed together with the inactive AI routines and
Cultural Missionary calculations. The active Missionary modifier was moved
into the current Religious State modifier file. Holy Sites, their monthly state
ownership scan, modifiers, panel, diagnostic hooks, and English localization were
removed; the new Religious State system is now the sole religious progression loop.
