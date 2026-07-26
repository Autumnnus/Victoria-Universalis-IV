# Victoria Universalis IV — Core Resource Systems Refactor Plan

> Status: design and implementation handoff document  
> Scope: Idea Points, religion/atheism, culture/National Identity, Ages/Splendor  
> Implementation has not started. Values in this document are initial balance
> targets unless explicitly marked as a locked decision.

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
- implement reusable cap/equilibrium helpers;
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
