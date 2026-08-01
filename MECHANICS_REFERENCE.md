# Victoria Universalis IV — Mechanics Reference

This is the durable, AI-oriented reference for the mod's active mechanics. Read it before answering, designing, debugging, or implementing work involving religion, National Identity/culture, Cultural or Religious Projects, idea groups, National Ideas, ages/Era Momentum, or the culture and religion actions in the state panel.

Last verified against the implementation: **2026-07-30**

## 1. How to use this reference

- This document defines system behavior, terminology, invariants, state, and source ownership.
- The linked implementation file is authoritative for exact script syntax and values changed after the verification date.
- Update this document in the same task whenever one of these mechanics changes.
- `IDEA_GROUP_BALANCE.md` describes balance intent. `KULTUR_SISTEMI_REHBERI_TR.md` is a player-facing Turkish culture guide. If either conflicts with live behavior, use the implementation and this reference.
- Do not extend retired systems merely because their definitions remain in the repository. See the legacy notes in sections 4.4 and 10.

## 2. Shared architecture

### Initialization and dispatch

`ve_initialize_country_system` initializes base resource variables, the idea system, the current National Idea profile, and National Identity. It runs for countries at game start, for released countries, for formed countries, and as a monthly compatibility fallback for countries created through an engine path without a dedicated hook.

| Cadence/hook | Entry point | Responsibilities |
| --- | --- | --- |
| Monthly | `ve_monthly_country_tick` | Update Religious Settlement, Piety Reform, Religious Project, National Insight, Cultural Mandate, National Cohesion, Cultural Project, Era Momentum, objective completion, and age-gated idea capacity. AI tries to buy the next idea in its current focus. |
| Half-yearly | `ve_half_yearly_country_tick` | AI chooses idea groups, religious programs/projects, identity/cultural projects, era rewards, and Golden Ages. |
| Half-yearly + 31 days | `ve_doctrine_ambient_half_yearly` | Runs the Phase 4 Idea Group ambient eligibility and frequency dispatcher for implemented pilot packs. |
| Half-yearly + 62 days | `ve_doctrine_journey_half_yearly` | Checks the Phase 5 Doctrine Journey offer queue. All three pilot packs—Industrialist, Academic, and Professional Army—are live. |
| Half-yearly + 93 days | `ve_era_crossroads_half_yearly` | Checks the Phase 6 Era Crossroads offer queue. All three Age packs are live. |
| Yearly | `ve_yearly_country_tick` | Compatibility reconciliation for progression-based idea-group capacity. Hidden age-transition events are also checked yearly. |
| Yearly + 45 days | `ve_tag_flavor_yearly` | Runs the Phase 7 country tag-flavor eligibility check and one 25% offer roll. TUR, JAP, and USA are live. |
| Church-and-State law activation | `on_law_activated` | Re-evaluate and synchronize the Religious Model immediately. |
| State owner change | `on_state_owner_change` | Remove the active Religious Project modifier from the captured target state. |
| Country formation | `on_country_formed` | Initialize systems and replace the old National Idea profile with the current tag's profile. |

Primary dispatch sources:

- `common/on_actions/ve_code_on_actions.txt`
- `common/scripted_effects/ve_set.txt`
- `common/scripted_effects/ve_monthly_effects.txt`

### Core country state

| Variable | Contract |
| --- | --- |
| `victoria_universalis_system_on` | Base VE country initialization marker. |
| `piety_bar_point` | Religious Settlement equilibrium meter, clamped to 0–100. It is not spendable. |
| `piety_reform_point` | Spendable Piety Reform, clamped to 0–500. |
| `idea_point_pool` | Spendable National Insight, clamped to 0–1000. |
| `culture_reform_point` | Spendable Cultural Mandate, clamped to 0–500. |
| `ve_national_cohesion` | National Cohesion equilibrium meter, clamped to 0–100. |
| `ve_splender_points` | Era Momentum stock. The misspelling is part of the script/save contract. |
| `idea_group_cap` | Maximum number of currently embraced idea groups. |
| `idea_group_unlocked` | Number of currently embraced idea groups. |
| `ve_idea_capacity_progress` | Current uncapped sum of purchased individual group-idea levels, 0–49. It earns permanent idea-group capacity. |
| `national_idea_pool` | Sum of purchased individual group-idea levels, capped at 21 for National Idea progression. |

## 3. Religion

The active religion design has four layers:

1. A law-driven **Religious Model**.
2. A 0–100 **Religious Settlement** equilibrium meter.
3. A 0–500 spendable **Piety Reform** stock.
4. A state-targeted **Religious Project**.

### 3.1 Religious Models

| Victoria 3 law | VE model | `ve_religious_model` | Base model effects |
| --- | --- | ---: | --- |
| `law_state_religion`, its variants, `law_millet_system`, and `law_people_of_the_book` | Confessional State | 1 | +5% Authority, +10% Conversion, +10% Devout political strength, -3% Migration Attraction, +5% radicals from Open Prejudice |
| `law_freedom_of_conscience` | Freedom of Conscience | 2 | +5% Migration Attraction, -15% Conversion, -25 Bureaucracy, -5% radicals from Open Prejudice |
| `law_total_separation` | Total Separation | 3 | -30% Conversion, +8% Migration Attraction, -10% Open Prejudice radicals, -5% Violent Hostility radicals |
| `law_state_atheism` and variants | State Atheism | 4 | +5% Tech Spread, +2% Education Access, -5% Authority, -10% Devout strength, +5% Open Prejudice radicals, +20% Conversion |

Invariants:

- Total Separation is the neutral model and cannot start a Targeted Religious Project.
- State Atheism is an aggressive secularization model, not the tolerant model. Vanilla `law_state_atheism` also contributes its own conversion behavior.
- Confessional State additionally receives exactly one small state-religion-family modifier.

Confessional faith-family packages:

| Family | Included religions | Effects |
| --- | --- | --- |
| Christian | Catholic, Protestant, Orthodox, Oriental Orthodox | +2.5% Bureaucracy, +2.5% Authority |
| Islamic | Sunni, Shiite | +3% Tax Capacity, +3% Influence |
| Jewish | Jewish | +3% Migration Attraction, +3% Tech Spread |
| Dharmic | Hindu, Sikh | +3 Legitimacy, -1% Mortality |
| Scholarly | Mahayana, Gelugpa, Theravada, Shinto, Confucian | +1% Education Access, +3% Tech Spread |
| Animist | Animist | +5% Conscription Rate, +2.5% Authority |

### 3.2 Model transitions and Religious Settlement

Initial setup derives the model from the current law and sets Religious Settlement to 50.

When the model changes:

- remove all programs from the previous model;
- remove settlement and faith-family modifiers;
- cancel an active Religious Project without the normal cancellation penalty;
- set Religious Settlement to 35;
- apply a Religious Settlement Crisis.

Crisis duration:

| Destination model | Duration |
| --- | ---: |
| Confessional | 48 months |
| Freedom or Separation | 36 months |
| State Atheism | 36 months normally; 60 months if literacy is below 50% or Devout clout is at least 20% |

The crisis applies -50 Bureaucracy, -50 Authority, and -5% Law Enactment Success.

A real model change also starts `ve_je_religious_settlement_transition`; initial setup does not. This modifier-authoritative Journey:

- lasts as long as `ve_religious_settlement_crisis_mdf`, while its own month counter is presentation/milestone state only;
- dispatches exactly two model-specific milestone events at months 12/24, 16/32, or 20/40 for a 36-, 48-, or 60-month transition;
- refreshes the same JE, target model, duration, and milestone state if Church and State changes again during an active transition;
- cancels an open old-model milestone popup when its stored destination no longer matches;
- closes as success at Settlement 60+, neutral at 26–59, or crisis at 25 or lower;
- never removes, reapplies, shortens, or extends the core crisis modifier;
- does not backfill a Journey for transitions already active when the feature is added.

Milestone choices are bounded to one of three budgets: spend 10 Piety Reform for +3 Settlement, gain 5 Piety Reform for -3 Settlement, or—when a model-fit Idea is present—spend 5 Piety Reform for +2 Settlement. The crisis closure's default can instead radicalize 0.25% of the country's population. All resource and meter changes use separate transition helpers and clamp to their normal ranges.

Religious Settlement is an equilibrium meter:

| Model | Base equilibrium |
| --- | ---: |
| Confessional | 55 |
| Freedom | 55 |
| Separation | 60 |
| State Atheism | 45 |

Model support and common country conditions then adjust the equilibrium:

- Confessional responds strongly to Devout approval and clout.
- State Atheism benefits from literacy and Intelligentsia approval, and is harmed by strong Devout clout.
- Freedom and Separation benefit from low turmoil.
- Legitimacy and healthy bureaucracy help every model.
- Turmoil, transition crisis, and program implementation strain reduce equilibrium.

The final equilibrium is clamped to 15–85. Each month, the meter moves 20% of the distance toward equilibrium, rounded and clamped to a monthly change of -5 to +5.

Settlement tiers:

| Tier | Result |
| --- | --- |
| 75+ | Confessional: +5% Authority/+5 Legitimacy; Freedom: +5% Migration Attraction/+5 Legitimacy; Separation: +5% Law Success/+5 Legitimacy; Atheism: +5% Tech Spread/+5% Bureaucracy |
| 26–74 | Base model effects only |
| 25 or lower | -5 Legitimacy and -5% Law Enactment Success |

The model and tier modifiers are applied by `ve_sync_religious_settlement_modifiers`, reached through `ve_sync_religious_state_if_needed` from the monthly tick and from `on_law_activated`. That wrapper was missing until 2026-07-28, so the settlement and tier modifiers were never actually granted; it now exists and records what it applied in `ve_synced_religious_model` and `ve_synced_settlement_tier` (tier 1 = 75+, 2 = 26–74, 3 = 25 or lower) so the sync only re-runs when the model or tier changes. The National Identity side uses the same pattern with `ve_synced_identity_model` / `ve_synced_identity_tier`.

### 3.3 Piety Reform and Religious Programs

Monthly Piety Reform:

- base +2;
- legitimacy contributes +2, +1, or -1;
- healthy administration contributes +2, otherwise -2;
- Devout approval contributes +1 or -1;
- raw monthly result is clamped to 1–8;
- income is multiplied by 0.5 at 400+ and by 0 at 500.

Each model has eight permanent programs. Purchasing one:

- costs 25 Piety Reform;
- applies 24 months of `ve_religious_program_strain_mdf`;
- blocks another program while the strain is active;
- is removed when the Religious Model changes.

| Slot | Confessional | Freedom | Separation | Atheism |
| ---: | --- | --- | --- | --- |
| 1 | Sacred Administration | Interfaith Councils | Civil Code | Scientific Administration |
| 2 | Parish Schools | Sanctuary Charter | Open Registry | Civil Registry |
| 3 | Charity Networks | Shared Schools | Neutral Administration | Public Education Campaign |
| 4 | Sacred Community | Equal Civic Rituals | Common Ceremony | Secular Welfare |
| 5 | Missionary Orders | Open Public Service | Public Schooling | Civic Morality |
| 6 | Faithful Service | Diplomatic Toleration | Even-Handed Diplomacy | Academic Freedom |
| 7 | Ecclesiastical Diplomacy | Plural Administration | Civic Trust | Anti-Clerical Campaign |
| 8 | Orthodoxy and Law | Rights Arbitration | Constitutional Guarantee | Public Ethics Commission |

The affordability trigger requires **25 Piety Reform**. `ve_religious_program_cost_tt` said “at least 50” until 2026-07-29 and now states 25; the Turkish file already said 25. 25 is the implemented behavior.

Exact program modifier values:

- `common/static_modifiers/ve_religious_state.txt`
- `localization/english/ve_religion_l_english.yml`

### 3.4 Targeted Religious Project

A country may run only one Religious Project. It is started from an owned state's panel.

Start requirements:

- the state is owned by the acting country;
- no other Religious Project is active;
- no 24-month project cancellation backlash is active;
- the model is Confessional, Freedom, or State Atheism;
- the state's share of the country's own religion is below 90%;
- the country can pay the model-specific Piety Reform cost.

| Model | Project type | Up-front cost |
| --- | --- | ---: |
| Confessional | Confessional Conversion | 125 |
| Freedom | Freedom Outreach | 100 |
| State Atheism | Secularization Campaign | 150 |

While active:

- country: -50 Bureaucracy and -25 Authority;
- target state: +20% Conversion and +20% to three hostility/radicalism channels;
- progress runs from 0 to 100;
- monthly progress is clamped to 1–7;
- administration, legitimacy, model-fit Devout/literacy conditions, and high Settlement increase progress;
- radical religious movements, low Settlement, and target-state turmoil reduce progress;
- a `ve_je_religious_project` Journal Entry mirrors the authoritative project progress and dispatches project incidents.

Religious Project incident lifecycle:

- a newly started project has a 3-month incident grace period;
- each incident starts a 6-month shared cooldown;
- at most three incidents may be created during one project;
- each normal/crisis event has a 5-year country cooldown, each rare breakthrough has a 10-year country cooldown, and every event has a once-per-project flag;
- the Confessional-specific normal-event pool contains `ve_rel_evt.1` through `ve_rel_evt.6`; every pool entry has weight 35 against a no-event weight of 1000 and its own progress/condition gate;
- `ve_rel_evt.7` is a weight-20 crisis below 70 progress when Settlement is 25 or lower, target turmoil is at least 25%, and administration, legitimacy, or radical religious movements are also failing; it can invoke the normal cancellation effect or continue at a resource, progress, Settlement, and/or radical cost;
- `ve_rel_evt.8` is a weight-2 breakthrough at 70+ progress when Settlement and Legitimacy are at least 75, administration is healthy, target turmoil is below 5%, and Nationalist VII is active; its options add either 25 progress/1 Settlement or 10 progress/4 Settlement, with progress routed through the core finish resolver and no Piety Reform award;
- Freedom Outreach and Secularization Campaign share `ve_rel_evt.40` through `ve_rel_evt.42` as weight-35 administrative/social incidents and `ve_rel_evt.43` as a weight-20 crisis; their options use the same incident cap, shared cooldown, once-per-project flags, bounded Piety/Settlement/progress changes, and telemetry layer as the Confessional pilot;
- Freedom Outreach additionally has `ve_rel_evt.100` and `ve_rel_evt.101` as weight-35 pluralism incidents and `ve_rel_evt.102` as a weight-2, 10-year-cooldown breakthrough requiring 70 progress, 75 Settlement, 75 Legitimacy, healthy administration, target turmoil below 5%, and Reformist VII; it never forces conversion, and breakthrough progress is routed through the core finish resolver;
- Secularization Campaign additionally has `ve_rel_evt.150` and `ve_rel_evt.151` as weight-35 education/property incidents and `ve_rel_evt.152` as a weight-2, 10-year-cooldown breakthrough requiring 70 progress, 70 Settlement, 75 Legitimacy, healthy administration, target turmoil below 5%, and Academic VII; the coercive property option trades 4 Settlement, state radicals, and 30 months of -1 Devout Approval for progress, while breakthrough progress uses the core finish resolver;
- `ve_rel_evt.5` and `ve_rel_evt.6` may apply a 30-month Devout modifier worth +1 or -1 Approval;
- gameplay-neutral `ve_evt_tm_rel_*` telemetry variables count starts, resolutions, event classes, crisis choices, actual event Piety changes after clamping, and monthly project duration; dated `VEU4_PROJECT_*` lines record begin/event/option/resolution observations in `debug.log`;
- all persistent feature telemetry increments use the save-compatible `ve_tm_change_country_variable` helper, which creates a missing numeric counter before its first mutation; Project incident/session cleanup removes timed modifiers only when they are present;
- the Project JE progress bars use feature-local, context-free progress descriptions rather than `journal_entry_goal_progress_integer`, preventing outliner/Journal rendering without a `JournalEntry` data context from spamming the runtime log;
- normal completion resolves the JE as success, normal cancellation as failure, and Religious Model cancellation as silent invalidation;
- projects already active when this feature is added do not receive a JE mid-progress; their first subsequent project uses the new lifecycle.

Completion:

| Project | Outcome |
| --- | --- |
| Confessional Conversion | Convert 5% of the target state's population to the country's state religion, add small radicals, refund 20 Piety Reform, add 5 Settlement |
| Freedom Outreach | No forced conversion; add state loyalists, refund 20 Piety Reform, add 7 Settlement |
| Secularization Campaign | Convert 5% to `rel:atheist`, add small radicals, refund 25 Piety Reform, add 8 Settlement |

Nationalist idea VII alone adds 2 percentage points to coercive conversion projects. The total converted share is the state-scope script value `ve_religious_project_conversion_amount` (5% base, 7% with Nationalist VII) in `common/script_values/ve_religious_project_values.txt`. Nationalist II remains a passive +15% Conversion/+15% Assimilation modifier; it does not alter project outcomes.

Normal cancellation:

- no Piety Reform refund;
- -5 Religious Settlement;
- 24-month backlash: -50 Bureaucracy, -50 Authority, -3% Law Enactment Success.

Primary sources:

- `common/scripted_triggers/ve_religious_state_triggers.txt`
- `common/script_values/ve_religious_state_values.txt`
- `common/script_values/ve_religious_project_values.txt`
- `common/scripted_effects/ve_religious_state_effects.txt`
- `common/scripted_effects/ve_project_event_effects.txt`
- `common/scripted_effects/ve_project_event_telemetry_effects.txt`
- `common/scripted_effects/ve_transition_journey_effects.txt`
- `common/scripted_triggers/ve_project_event_triggers.txt`
- `common/scripted_triggers/ve_transition_journey_triggers.txt`
- `common/journal_entries/ve_project_journal_entries.txt`
- `common/journal_entries/ve_transition_journal_entries.txt`
- `common/static_modifiers/ve_project_event_modifiers.txt`
- `common/scripted_guis/ve_religious_state.txt`
- `common/customizable_localization/ve_religious_state_cl.txt`
- `common/static_modifiers/ve_religious_state.txt`
- `events/ve_religious_project_events.txt`
- `events/ve_religious_transition_events.txt`
- `gui/ve_panel_religion.gui`
- `localization/english/ve_religion_l_english.yml`
- `localization/english/ve_project_events_l_english.yml`
- `localization/turkish/ve_project_events_l_turkish.yml`
- `localization/english/ve_transition_journeys_l_english.yml`
- `localization/turkish/ve_transition_journeys_l_turkish.yml`

## 4. Culture and National Identity

The active culture design consists of:

1. one always-active **Identity Model**;
2. a 0–500 **Cultural Mandate** stock;
3. a 0–100 **National Cohesion** equilibrium meter;
4. countrywide and state-targeted **Cultural Projects**.

### 4.1 Identity Models

Initial model selection:

- Ethnostate or National Supremacy → Ethnic Nation;
- Multiculturalism → Civic Nation;
- all other citizenship laws → Composite State.

| Model | `ve_identity_model` | Base effects |
| --- | ---: | --- |
| Ethnic Nation | 1 | +15% Assimilation, +5% Authority, -5% Migration Attraction, +5% radicals from Open Prejudice |
| Civic Nation | 2 | +7% Migration Attraction, +1% Education Access, -10% Assimilation, -5% Authority, -50 Bureaucracy |
| Composite State | 3 | -10% Cultural Erasure and Second-Rate Citizenship radicals, +5% Influence, -15% Assimilation, -5% Authority, -75 Bureaucracy |

Changing models:

- costs 200 Cultural Mandate;
- is blocked by Identity Transition Backlash;
- sets National Cohesion to 35;
- cancels the active Cultural Project without its normal cancellation penalty;
- applies 60 months of -100 Bureaucracy, -50 Authority, and -5% Law Enactment Success.

Each real model change also starts `ve_je_national_compact_transition`; initial identity initialization does not. The authoritative duration remains the 60-month `ve_identity_transition_backlash_mdf`. The JE dispatches exactly two destination-specific milestone events at months 20 and 40, then closes as success at Cohesion 60+, neutral at 26–59, or crisis at 25 or lower. It never changes the backlash duration or reverses the chosen Identity Model, and transitions already active when the feature is added are not backfilled.

Identity milestone choices mirror the Religious Journey's bounded budget: spend 10 Cultural Mandate for +3 Cohesion, gain 5 Mandate for -3 Cohesion, or use a model-fit Idea to spend 5 Mandate for +2 Cohesion. The crisis closure's default can radicalize 0.25% of the country's population. A closure popup retains only a short pending context; beginning another transition clears it so an old popup cannot mutate the new session.

### 4.2 Cultural Mandate

Monthly Mandate:

- base +2;
- legitimacy and administration can add or subtract;
- model/society fit uses literacy, primary-culture share, and plurality;
- turmoil, transition backlash, and radical cultural movements subtract;
- citizenship-law alignment adds +1 or can subtract -1;
- raw result is clamped to 1–8;
- income is multiplied by 0.5 at 400+ and by 0 at 500.

Mandate is spent on model changes and Cultural Projects. Merely holding a high stock does not force a model change.

### 4.3 National Cohesion

Initial Cohesion is 50. Its equilibrium combines:

- common conditions: legitimacy, administration, turmoil, transition backlash, and radical cultural movements;
- model-specific conditions:
  - Ethnic prefers restrictive citizenship laws and a high primary-culture share;
  - Civic prefers Multiculturalism, literacy, and accepted minorities;
  - Composite prefers intermediate citizenship laws, healthy bureaucracy, and a genuinely plural population.

The equilibrium is clamped to 15–85. Cohesion moves 20% of the gap each month, with a monthly clamp of -5 to +5.

| Tier | Result |
| --- | --- |
| 75+ Ethnic | +5% Conscription Rate, +3 Legitimacy |
| 75+ Civic | +5% Qualifications, +3 Legitimacy |
| 75+ Composite | +5% Influence, +3 Legitimacy |
| 26–74 | Base model effects only |
| 25 or lower | -5 Legitimacy, -5% Law Enactment Success |

### 4.4 Cultural Projects

General rules:

- only one Cultural Project may be active;
- its Mandate cost is paid immediately;
- National Curriculum and Shared Symbols cannot be started again while their own completion modifier is active; they become available again after its 10-year or 8-year duration expires;
- completing a targeted project records the target culture on that State, so that State/culture pair cannot be selected again, while the same culture remains eligible in another State;
- an active project applies -75 Bureaucracy and -25 Authority;
- progress runs from 0 to 100 and monthly progress is clamped to 1–7;
- administration, legitimacy, model/society fit, and high Cohesion help progress;
- radical cultural movements and target-state turmoil slow progress;
- normal cancellation gives no refund, removes 5 Cohesion, and applies a 24-month backlash;
- backlash applies -50 Bureaucracy, -25 Authority, and -3% Law Enactment Success;
- a `ve_je_cultural_project` Journal Entry mirrors the authoritative project progress and dispatches project incidents.

Cultural Project incident lifecycle:

- a newly started project has a 3-month incident grace period;
- each incident starts a 6-month shared cooldown;
- at most three incidents may be created during one project;
- each normal/crisis event has a 5-year country cooldown, each rare breakthrough has a 10-year country cooldown, and every event has a once-per-project flag;
- countrywide projects receive the JE without a state target and use a separate eligibility/context path that never reads target-state or target-culture scopes;
- the Equal Citizenship-specific normal-event pool contains `ve_cul_evt.1` through `ve_cul_evt.6`; every pool entry has weight 35 against a no-event weight of 1000 and its own progress/condition gate;
- `ve_cul_evt.7` is a weight-20 crisis below 70 progress when Cohesion is 25 or lower, target turmoil is at least 25%, and a radical cultural movement is active; it can invoke the normal cancellation effect or continue at a resource, progress, Cohesion, and/or target-culture radical cost;
- `ve_cul_evt.8` is a weight-2 breakthrough at 70+ progress when Cohesion and Legitimacy are at least 75, administration is healthy, target turmoil is below 5%, and Reformist VII, Academic VII, or Welfare VI is active; its options add either 25 progress/1 Cohesion or 10 progress/4 Cohesion, with progress routed through the core finish resolver and no Cultural Mandate award;
- Ethnic Integration Campaign and Constituent Compact share `ve_cul_evt.40` and `ve_cul_evt.41` as weight-35 school/registry incidents and `ve_cul_evt.42` as a weight-20 crisis requiring progress below 70, Cohesion at 25 or lower, target turmoil of at least 25%, and radical cultural-movement pressure; target-pop effects are restricted to the stored culture, and the crisis uses the existing normal cancellation/backlash path;
- Ethnic Integration additionally receives the weight-35 `ve_cul_evt.50` surname/language directive at 15–65 progress and `ve_cul_evt.51` conscription-register dispute at 25–75 progress; their coercive paths trade up to +7 progress for Cohesion and target-culture radical costs, while Nationalist V or Mass Conscription V can unlock a Mandate-funded service compromise;
- Constituent Compact additionally receives the weight-35 `ve_cul_evt.100` constituent delegation at 10–65 progress and `ve_cul_evt.101` dual-administration incident at 25–75 progress during an active or approaching Bureaucracy shortage; Parliamentary IV, Diplomatic V, and Bureaucratic V provide model-fit Mandate-funded compromises;
- National Curriculum and Shared Symbols share the weight-35 `ve_cul_evt.150` provincial-implementation incident at 15–65 progress; National Curriculum additionally receives the weight-35 `ve_cul_evt.151` language-of-instruction dispute at 20–75 progress, while Shared Symbols receives the weight-35 `ve_cul_evt.160` representation dispute over the same range; these countrywide events affect only Mandate, Cohesion, and project progress and never create pop effects;
- `ve_cul_evt.4` may trade +5 project progress for a 24-month target-state modifier worth -5% Tax Capacity;
- gameplay-neutral `ve_evt_tm_cul_*` telemetry variables count starts, resolutions, event classes, crisis choices, actual event Mandate changes after clamping, and monthly project duration; dated `VEU4_PROJECT_*` lines record begin/event/option/resolution observations in `debug.log`;
- Cultural Project cleanup checks each target-state and incident cooldown modifier before removal, so initializing or clearing an inactive project remains runtime-log neutral;
- normal completion resolves the JE as success, normal cancellation as failure, and Identity Model cancellation as silent invalidation;
- projects already active when this feature is added do not receive a JE mid-progress.

Countrywide projects:

| Project | Cost | Completion | Timed result |
| --- | ---: | --- | --- |
| National Curriculum | 100 | +20 Mandate, +5 Cohesion | 10 years: +2% Education Access, +5% Qualifications, -25 Bureaucracy |
| Shared Symbols | 75 | +20 Mandate, +7 Cohesion | 8 years: +10% loyalists from fully accepted pops, +25 Authority |

State targeting rules:

- the state is owned by the acting country;
- a non-primary culture represents at least 5% of the state;
- the largest eligible culture is selected automatically;
- Composite cannot select a culture already stored in `ve_recognized_constituent_cultures`;
- the Ethnic project stores a random primary culture as its assimilation destination.

| Model | Project | Cost/additional gate | Completion |
| --- | --- | --- | --- |
| Ethnic | Ethnic Integration Campaign | 125 Mandate | Convert 5% of target culture pops to the stored primary culture (7% with Nationalist VII); +25 Mandate, +8 Cohesion, radicals, and a 10-year assimilation result |
| Civic | Equal Citizenship Initiative | 100 Mandate | +15 Acceptance for 10 years, state loyalists, +25 Mandate, +10 Cohesion, and a 10-year qualifications/migration result |
| Composite | Constituent Compact | 150 Mandate and at least 40 Cohesion | Permanent +15 Acceptance, add culture to the constituent list, state loyalists, +30 Mandate, +12 Cohesion |

Primary sources:

- `common/scripted_effects/ve_national_identity_effects.txt`
- `common/scripted_triggers/ve_national_identity_triggers.txt`
- `common/script_values/ve_national_identity_values.txt`
- `common/scripted_effects/ve_cultural_project_effects.txt`
- `common/scripted_effects/ve_project_event_effects.txt`
- `common/scripted_effects/ve_project_event_telemetry_effects.txt`
- `common/scripted_effects/ve_transition_journey_effects.txt`
- `common/scripted_triggers/ve_cultural_project_triggers.txt`
- `common/scripted_triggers/ve_project_event_triggers.txt`
- `common/scripted_triggers/ve_transition_journey_triggers.txt`
- `common/script_values/ve_cultural_project_values.txt`
- `common/journal_entries/ve_project_journal_entries.txt`
- `common/journal_entries/ve_transition_journal_entries.txt`
- `common/static_modifiers/ve_national_identity.txt`
- `common/static_modifiers/ve_cultural_projects.txt`
- `common/static_modifiers/ve_project_event_modifiers.txt`
- `common/scripted_guis/ve_national_identity.txt`
- `common/scripted_guis/ve_cultural_projects.txt`
- `common/customizable_localization/ve_national_identity_cl.txt`
- `common/customizable_localization/ve_cultural_projects_cl.txt`
- `events/ve_cultural_project_events.txt`
- `events/ve_identity_transition_events.txt`
- `gui/ve_panel_culture.gui`
- `localization/english/ve_culture_l_english.yml`
- `localization/english/ve_project_events_l_english.yml`
- `localization/turkish/ve_project_events_l_turkish.yml`
- `localization/english/ve_transition_journeys_l_english.yml`
- `localization/turkish/ve_transition_journeys_l_turkish.yml`

### 4.5 Retired culture path

`reform_limiter` and `reform_bar_effects` were deleted on 2026-07-28: they had no caller and their `var:culture_reform_value` / `var:selected_reform_value` reads logged "variable is used but never set" on every load. The repository still contains `national_supremacy_mdf_*`, `intellectual_nation_mdf_*`, and `bar_*` definitions, which likewise have no active GUI, scripted-GUI, or pulse call path.

Do not add new culture work to the old ±7 reform bar. Extend Identity Model, Cultural Mandate, National Cohesion, or Cultural Projects instead.

## 5. State-panel culture and religion actions

`gui/states_panel.gui` adds two adjacent action cards to the state overview:

- Targeted Religious Project;
- Targeted Cultural Project.

Each card:

- shows Start only for a state owned by the player;
- uses a scripted GUI to itemize unmet requirements in its tooltip;
- shows a confirmation-based Cancel flow on the active target state;
- shows country-level 0–100 project progress on the active target state.

Religious Start validates:

- an enabled Religious Model;
- no active Religious Project;
- no backlash;
- model-specific Piety Reform;
- less than 90% of the country's religion in that state.

Cultural Start validates:

- no active Cultural Project;
- no backlash;
- model-specific Mandate;
- 40 Cohesion for Composite;
- an eligible non-primary culture at 5% or more.

Sources:

- `gui/states_panel.gui`, VE block approximately lines 1266–1421
- `common/scripted_guis/ve_religious_state.txt`
- `common/scripted_guis/ve_cultural_projects.txt`
- `localization/english/ve_gui_l_english.yml`

## 6. Idea groups

### 6.1 National Insight

`idea_point_pool` is clamped to 0–1000.

Monthly generation:

- base +6;
- literacy +1 to +4;
- Schools institution +0 to +3;
- population-scaled university capacity +0 to +2;
- administration +1 or -2;
- legitimacy +2, +1, -1, or -2;
- Intelligentsia approval +1 or -1;
- loans -1;
- turmoil -1 or -2;
- 24-month Doctrine Implementation Strain -2;
- raw total clamped to 2–18;
- stock multiplier: 0.5 at 750+, 0.25 at 900+, 0 at 1000.

| Level | I | II | III | IV | V | VI | VII |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Insight cost | 200 | 250 | 300 | 375 | 450 | 550 | 675 |

A completed group costs 2800 total Insight. Every level purchase applies 24 months of Doctrine Implementation Strain. While that modifier is active, no other group idea can be purchased; it therefore acts as both the income penalty and the global implementation cadence.

### 6.2 Group capacity

Countries start with one group slot. Capacity is earned permanently from current doctrine investment (`ve_idea_capacity_progress`):

| Capacity | Required purchased group-idea levels | Additional gate |
| ---: | ---: | --- |
| 1 | Starting capacity | — |
| 2 | 4 | — |
| 3 | 8 | — |
| 4 | 13 | — |
| 5 | 19 | Age 2 |
| 6 | 26 | Age 2 |
| 7 | 34 | Age 3 |

Embracing a group costs no Insight. It occupies one slot and enables purchases in that group.

Capacity is raised immediately after an idea purchase and reconciled monthly/yearly for age transitions and save compatibility. It never decreases. Cancelling ideas can lower current doctrine investment but does not revoke capacity already institutionalized. Existing saves retain a higher capacity earned under the retired calendar system; fresh or late-created countries do not receive calendar catch-up slots.

The threshold gaps and the 24-month implementation cadence prevent a full 1000-point Insight bank from granting several capacity tiers in one burst. Concentrating purchases in one group reaches Ambition sooner but pays the expensive high-level costs; spreading purchases reaches capacity thresholds sooner but delays group capstones.

Player-facing capacity tooltips are dynamic rather than a bare threshold list. They show used and free slots, current investment, the next slot number, its threshold, remaining purchases, any Age gate, maximum-capacity state, and whether Doctrine Implementation currently blocks another purchase. Readout helpers live in `common/script_values/ve_script_values.txt` and `common/customizable_localization/ve_idea_capacity_cl.txt`.

The Ideas-panel overview bar and its `ve_max_idea_text` label track embraced groups against the campaign maximum of 7 (`0/7` through `7/7`). Current usable capacity remains a separate `used / idea_group_cap` readout in its tooltip and in the topbar.

### 6.3 Group catalog and state data carriers

The idea panel builds cards from global lists of real state scopes. Each listed state is a UI data carrier holding an `idea_group` flag. Ownership of the carrier state does not control access to the group.

| Category | Group | Carrier state |
| --- | --- | --- |
| Production | Industrialist | `STATE_LOUISIANA` |
| Production | Mercantile | `STATE_LANCASHIRE` |
| Production | Financial | `STATE_LOMBARDY` |
| Production | Infrastructure | `STATE_RHINELAND` |
| Production | Extraction | `STATE_URAL` |
| Production | Labour | `STATE_EAST_ANGOLA` |
| Production | Agrarian | `STATE_PUNJAB` |
| Society | Academic | `STATE_MINSK` |
| Society | Bureaucratic | `STATE_NEW_YORK` |
| Society | Parliamentary | `STATE_LOWER_EGYPT` |
| Society | Welfare | `STATE_PROVENCE` |
| Society | Diplomatic | `STATE_HOME_COUNTIES` |
| Society | Nationalist | `STATE_VIRGINIA` |
| Society | Reformist | `STATE_NORMANDY` |
| Military | Offensive | `STATE_HOLLAND` |
| Military | Defensive | `STATE_BALUCHISTAN` |
| Military | Naval | `STATE_EAST_BENGAL` |
| Military | Professional Army | `STATE_DOBRUDJA` |
| Military | Mass Conscription | `STATE_ILE_DE_FRANCE` |
| Military | Colonial | `STATE_BASRA` |
| Military | War Economy | `STATE_RUHR` |

Carrier definitions: `common/history/states/ve_states.txt`.

### 6.4 Technology gates and mutually exclusive paths

The following groups require the country itself to have researched the named vanilla technology. The Ideas panel shows the exact technology name in the locked button tooltip.

| Idea Group | Required technology |
| --- | --- |
| Labour | Labor Movement |
| Welfare | Human Rights |
| Nationalist | Nationalism |
| Reformist | Egalitarianism |
| Mass Conscription | Enlistment Offices |
| Colonial | Quinine |
| War Economy | War Propaganda |

Extraction can be embraced without a technology gate, but its seventh level requires Dynamite.

Mutually exclusive pairs:

- Agrarian / Extraction;
- Nationalist / Reformist;
- Professional Army / Mass Conscription.

Cancelling the chosen side reopens the opposing path.

### 6.5 Progression, Ambition, and cancellation

- Each group uses a numeric `*_idea` variable from 0 to 7.
- Each purchase grants a permanent `*_idea_N_mdf`.
- Level 7 sets `*_idea_completed` and grants the permanent `*_ambition_mdf` capstone.
- Cancellation removes the group's modifiers, Ambition, completion marker, and access variable.
- Spent National Insight is never refunded.
- Group count, current doctrine investment, and National Idea progress are recalculated; falling below a National Idea threshold may revoke that National Idea.
- Earned idea-group capacity is permanent and is not revoked by cancellation.

Exact group modifiers: `common/static_modifiers/ve_group_ideas.txt`.

Balance contract after the 2026-07-29 review:

- high-leverage completed-group totals are kept near 20–30%, with narrower building, trade, colony, and terrain bonuses allowed to reach higher conditional totals;
- Parliamentary totals are +20% Law Enactment Speed and +10 percentage points of Law Enactment Success;
- Labour totals +3 percentage points of Working Adult Ratio;
- Bureaucratic totals +25% Bureaucracy;
- Infrastructure totals +25% Infrastructure;
- Welfare totals -6% Mortality and +30% Migration Pull;
- Diplomatic totals +25% Infamy Decay, -10% Infamy Generation, and +20% Influence;
- Offensive and Defensive each total +20% to their principal army multiplier;
- Mass Conscription totals +40% Conscription Rate and +3 Conscription Center maximum levels;
- Nationalist totals +25% passive Conversion and Assimilation; its VII capstone raises coercive religious and ethnic project outcomes from 5% to 7%;
- flat coal, iron, sulfur, explosives, and steel output bonuses were replaced with building throughput so they scale with production methods;
- bonuses that unintentionally reduced urbanization, government or military wages, welfare payments, or commercial arable land were replaced with positive infrastructure, administration, health, doctrine-spread, or subsistence-production effects.

### 6.6 Idea-group integration with reform systems

Ideas retain their indirect effects through bureaucracy, legitimacy, literacy and social support. Direct bonuses are reserved for doctrines that match the active model, and are visible in the relevant resource/project breakdowns.

| System | Direct contributions | Cap |
| --- | --- | ---: |
| Piety Reform income | Nationalist V in Confessional/State Atheism; Reformist V in Freedom/Total Separation | +1/month |
| Cultural Mandate income | Nationalist V in Ethnic; Reformist V in Civic/Composite; Academic V in Civic | +2/month |
| Religious Project progress | Nationalist VII in Confessional/State Atheism; Reformist VII in Freedom; Academic VII in State Atheism | +2/month |
| Cultural Project progress | Nationalist VII in Ethnic; Reformist VII in Civic/Composite; Academic VII and Welfare VI in Civic; Diplomatic VI in Composite | +2/month |

Level-IV groups also give +1 Era Momentum per month while their assigned age is current, capped at +2 from idea groups: Age 1 uses Industrialist, Mercantile, Financial, Infrastructure, Academic, Bureaucratic and Parliamentary; Age 2 uses Extraction, Agrarian, Labour, Welfare, Diplomatic, Nationalist, Reformist and Colonial; Age 3 uses Offensive, Defensive, Naval, Professional Army, Mass Conscription and War Economy.

Ideas do not directly alter Religious Settlement, National Cohesion, age-objective satisfaction, or the one-time +50 objective completion reward.

### 6.7 Idea Group ambient event dispatcher

The Phase 4 ambient carrier is attached to the country half-yearly pulse with a
31-day delay. An initialized country without
`ve_doctrine_ambient_cooldown_mdf` is eligible when it has at least one
available event from Industrialist, Agrarian, Academic, Nationalist, Reformist,
or Professional Army.

The carrier makes one 25% global roll and then selects only an eligible
category using the structural Production/Society/Military weights of 2/3/1.
Eligible groups inside a category have equal weight. The shared cooldown is 36 months and is
applied by `ve_doctrine_ambient_begin_event` only when a real content event
opens; it is not applied for an empty dispatch branch. The same helper increments
the gameplay-neutral `ve_idea_tm_ambient_events` counter.

The Production pilot is live:

- Industrialist: `ve_idea_evt.10` dilemma, `.11` opportunity, `.12` setback;
- Agrarian: `ve_idea_evt.60` dilemma, `.61` opportunity, `.62` setback.

The Society pilot is also live:

- Academic: `ve_idea_evt.20` dilemma, `.21` opportunity, `.22` setback;
- Nationalist: `ve_idea_evt.30` dilemma, `.31` opportunity, `.32` setback;
- Reformist: `ve_idea_evt.40` dilemma, `.41` opportunity, `.42` setback.

The Military pilot is live:

- Professional Army: `ve_idea_evt.50` dilemma, `.51` opportunity, `.52`
  setback.

All six pilot groups are therefore active. Category weights 2/3/1 now map
exactly to two Production groups, three Society groups, and one Military group.
Professional Army's dilemma is the one bounded exception to the generic
dilemma shape: merit costs 25 Insight, gives +5% Training Rate for 24 months,
and applies -1 Armed Forces Approval for 24 months; seniority gives +1 Approval
for 24 months and -5% Training Rate for only 12 months; the Idea V route costs
10 Insight and gives +5% Training Rate for 24 months without Approval change.

Dilemmas and setbacks require Idea II; opportunities require Idea IV. Their
efficient options require Idea V or VII and the corresponding 10 or 20 Insight.
Every event has a 10-year engine cooldown plus a 10-year timed dispatch variable
that lets the scripted pool exclude it before weighted selection. Cancelling the
relevant group invalidates an open popup. Every paid option re-checks both group
context and affordability before applying its hidden effect.

Phase 4 static acceptance passed on 2026-07-29: all 18 events, 54 options,
dispatch/cooldown paths, Idea II/IV event gates, Idea V/VII efficient-option
gates, Insight budgets and clamp behavior, 15 modifier definitions, vanilla
modifier types and assets, and the matching 174-key English/Turkish localization
sets were verified. Runtime frequency and AI-distribution observation remains
deferred by user decision.

The common outcome layer is also live and ready for those packs:

- `ve_doctrine_ambient_change_national_insight` applies a signed delta, clamps
  Insight to 0–1000, and adds the actual post-clamp change to
  `ve_idea_tm_ambient_insight_net_total`;
- the event recorder applies the shared cooldown and increments total, group,
  and dilemma/opportunity/setback counters; option choices have a separate
  total counter;
- explicit Interest Group scopes can receive +1 or -1 Approval for 24 months;
- each pilot group has a positive and negative temporary modifier on one narrow
  axis: Manufacturing, University throughput, legitimacy loyalists/radicals,
  political-movement loyalists/radicals, Training Rate, or Agriculture. Every
  axis is bounded to ±5%; event content will own the 36-month positive and
  24-month negative durations.

Primary sources:

- `common/on_actions/ve_code_on_actions.txt`
- `common/on_actions/ve_doctrine_ambient_on_actions.txt`
- `common/scripted_triggers/ve_doctrine_ambient_triggers.txt`
- `common/scripted_effects/ve_doctrine_ambient_effects.txt`
- `common/static_modifiers/ve_doctrine_ambient_modifiers.txt`
- `events/ve_idea_ambient_events.txt`
- `localization/english/ve_idea_ambient_events_l_english.yml`
- `localization/turkish/ve_idea_ambient_events_l_turkish.yml`
- `common/script_values/ve_script_values.txt`
- `common/customizable_localization/ve_idea_capacity_cl.txt`
- `common/scripted_effects/ve_idea_effects.txt`
- `common/scripted_effects/ve_scripted_effects.txt`
- `common/scripted_guis/ve_idea.txt`
- `gui/ve_panel_ideas.gui`
- `localization/english/ve_idea_l_english.yml`
- `localization/english/ve_modifiers_l_english.yml`

### 6.8 Doctrine Journey lifecycle

Phase 5's shared Doctrine Journey lifecycle and all three pilot packs are live.
The country half-yearly pulse calls
`ve_doctrine_journey_half_yearly` after 62 days, separated from the 31-day
ambient carrier. An offer requires an initialized country, no active Journey,
no pending offer, current-age completion capacity below two, and an available
implemented pilot.

The common layer provides:

- equal-weight offer branches for Industrialist, Academic, and Professional
  Army;
- a 14-day pending-offer reservation;
- start, five-year defer, and group-permanent decline outcomes;
- one active Journey session with 0–60 progress and a 60-month counter;
- start-age snapshots and separate completion counters for Ages 1–3, clamped
  to two;
- three five-year JE shells with progress bars;
- shared begin, monthly tick, success, failure, and cleanup effects;
- offer/start/resolution telemetry and debug markers;
- matching English and Turkish localization.

The Industrialist pilot is live. Its **Standardizing the Factory System**
Journey requires Industrialist Idea IV and measures two monthly conditions:

- a population-scaled `bg_manufacturing` target of 10 levels below 5 million
  population, 25 at 5–20 million, 50 at 20–50 million, or 100 at 50 million
  and above;
- non-negative Bureaucracy, no approaching Bureaucracy shortage, and country
  Turmoil below 15%.

Meeting both conditions gives +2 monthly progress, one gives +1, and neither
gives 0. `ve_doctrine_journey.10` and `.11` dispatch once at 20 and 40
progress. Each has a free neutral default, a 15-Insight option for +4 progress,
and an Idea V/VII option that gives the same +4 progress for 10 Insight. Thus
milestones can accelerate the Journey by at most +8 progress and the doctrine
route is more efficient rather than stronger. Success grants only +40 National
Insight through a dedicated 0–1000 clamp and actual-delta telemetry helper.

The Academic pilot is also live. Its **Republic of Scholars** Journey requires
Academic Idea IV and measures:

- a population-scaled `bg_technology` target of 3 levels below 5 million
  population, 8 at 5–20 million, 15 at 20–50 million, or 25 at 50 million
  and above;
- Literacy of at least 50%, or an increase of at least five percentage points
  from the Journey's start snapshot.

`ve_doctrine_journey.20` and `.21` dispatch once at 20 and 40 progress. Their
free, paid, and Idea V/VII routes use the same neutral-default and 15/10
Insight-for-+4-progress budget as the Industrialist milestones, so their total
acceleration is likewise capped at +8. Success grants only +15 Era Momentum
through a dedicated actual-delta helper. It changes only `ve_splender_points`,
uses the live resource's non-negative invariant without adding an artificial
upper cap, and never mutates objective flags/counts or Golden Age state.

The Professional Army pilot is also live. Its **Reforming the General Staff**
Journey requires Professional Army Idea IV and measures:

- a population-scaled canonical `bt:building_barrack` target of 10 levels
  below 5 million population, 25 at 5–20 million, 50 at 20–50 million, or 100
  at 50 million and above;
- either the Professional Army law or General Staff technology.

War, conquest, casualties, and mobilized-unit counts are deliberately not
conditions. `ve_doctrine_journey.30` and `.31` dispatch once at 20 and 40
progress and use the same free/default, 15-Insight, and Idea V/VII 10-Insight
budget as the other pilots. Their combined acceleration is capped at +8.
Success grants only `ve_doctrine_journey_general_staff_reform_mdf` for 36
months, providing +7.5% Training Rate. It grants neither National Insight nor
Era Momentum.

Phase 5 static acceptance is complete: all 20 lifecycle, balance, localization,
source-reference, asset, structural, reward-exclusivity, failure-safety, and
cross-feature mutation checks pass. Runtime observations remain deferred by
user choice and do not block the static Phase 5 closure.

Primary sources:

- `common/on_actions/ve_code_on_actions.txt`
- `common/on_actions/ve_doctrine_journey_on_actions.txt`
- `common/scripted_triggers/ve_doctrine_journey_triggers.txt`
- `common/script_values/ve_doctrine_journey_values.txt`
- `common/scripted_effects/ve_doctrine_journey_effects.txt`
- `common/static_modifiers/ve_doctrine_journey_modifiers.txt`
- `common/journal_entries/ve_doctrine_journeys.txt`
- `events/ve_doctrine_journey_events.txt`
- `localization/english/ve_doctrine_journeys_l_english.yml`
- `localization/turkish/ve_doctrine_journeys_l_turkish.yml`

## 7. National Ideas

### 7.1 Progression contract

Every purchased individual group-idea level adds one to `national_idea_pool`. Completion of a group is not required.

| National Idea | Required total purchased group-idea levels |
| ---: | ---: |
| 1 | 3 |
| 2 | 6 |
| 3 | 9 |
| 4 | 12 |
| 5 | 15 |
| 6 | 18 |
| 7 + National Bonus | 21 |

The progression calculation is capped at 21. Cancelling a group can lower the pool and remove National Ideas above the new threshold. Two profile Traditions are granted independently during profile initialization.

### 7.2 Country profiles

| Profile | Tags | Modifier prefix |
| --- | --- | --- |
| British | GBR | `gbr_` |
| French | FRA | `fra_` |
| German | PRU, NGF, SGF, GER | `ger_` |
| Austrian | AUS | `aus_` |
| Russian | RUS | `rus_` |
| Turkish/Ottoman | TUR | `tur_` |
| Chinese/Qing | CHI | `qng_` |
| Japanese | JAP | `jap_` |
| American | USA | `usa_` |
| Spanish | SPA, IBE | `ve_spa_` |
| Italian | ITA | `ve_ita_` |
| Swedish/Scandinavian | SWE, SCA | `ve_swe_` |
| Indian | BIC, HND | `ve_ind_` |
| Mexican | MEX | `ve_mex_` |
| Brazilian | BRZ | `ve_bra_` |
| Dutch | NET | `ve_net_` |
| Belgian | BEL | `ve_bel_` |
| Persian | PER | `ve_per_` |
| Egyptian | EGY | `ve_egy_` |
| Korean | KOR | `ve_kor_` |
| Argentine | ARG | `ve_arg_` |
| Generic | Every other country | `generic_` |

Each profile contains:

- two starting Traditions;
- seven National Ideas at 3/6/9/12/15/18/21;
- one National Bonus at 21.

After formation, `ve_refresh_national_idea_profile` removes all possible old profile modifiers, selects the current tag's profile, recalculates progress, and reapplies earned modifiers.

Primary sources:

- `common/scripted_effects/ve_national_ideas.txt`
- `common/scripted_effects/ve_country_idea_profiles.txt`
- `common/scripted_effects/ve_scripted_effects.txt`
- `common/scripted_triggers/ve_national_idea_triggers.txt`
- `common/static_modifiers/ve_national_ideas.txt`
- `common/scripted_guis/ve_national_ideas.txt`
- `localization/english/ve_country_ideas_l_english.yml`
- `localization/english/ve_modifiers_l_english.yml`

## 8. Ages and Era Momentum

### 8.1 Calendar and transition contract

| Age | Dates | Active global |
| --- | --- | --- |
| Industry and Nations | 1836–1870 | `ve_age_1_started` |
| Empire and Mass Society | 1871–1905 | `ve_age_2_started` |
| Mass Politics and Total War | 1906–1936 | `ve_age_3_started` |

The yearly pulse checks hidden `dev.5` and `dev.6` on an AI country so each transition executes once globally. Human players receive `ve_ages.1` or `ve_ages.2`.

An age transition:

- removes reward modifiers from the previous age;
- resets Era Momentum to 0;
- resets the age reward purchase counter and cost ladder;
- resets the distinct-objective counter;
- removes the previous age's objective-completion flags;
- does not reset the once-per-game Golden Age lock;
- leaves a currently active 15-year Golden Age to expire normally.

`age_2_started_trigger` and `age_3_started_trigger` are permanent gate markers. Unlike `ve_age_N_started`, they are not removed.

### 8.2 Objectives and Momentum income

| Slot | Age 1: Industry and Nations | Age 2: Empire and Mass Society | Age 3: Mass Politics and Total War |
| ---: | --- | --- | --- |
| 1 | Peasant share below 40% | £100M GDP or peasant share below 25% | Universal Suffrage/Council Republic, or 75 Legitimacy in a Parliamentary/Presidential Republic |
| 2 | Slavery Banned and no Serfdom | 65% Literacy or Schools 4 | Any two of Health/Social Security/Workplace Safety/Schools at level 3 |
| 3 | 70 Legitimacy and healthy bureaucracy | Two subjects, or independent and recognized | One Power Plant if under 10M population, otherwise five |
| 4 | 50% Literacy or Schools 3 | Two Ports if under 10M, otherwise ten, or five interests | One Oil Rig or five Motor Industry levels |
| 5 | Three Railways if under 5M population, otherwise six | Below 5% turmoil and 60 Legitimacy | 50% Trench/Squad Infantry and 15% Shrapnel Artillery |
| 6 | Independent, below 5% turmoil, 65 Legitimacy | One of Health/Workplace Safety/Social Security at level 2 | 40 army units and five Arms Industry or three Munition Plant levels |
| 7 | Major/Great Power or five interests | 50% Skirmish/Trench Infantry and 10% Mobile Artillery | Major/Great Power, Power Bloc leader, or six interests |

Momentum rules:

- each currently satisfied objective grants +1 Era Momentum per month;
- each matching level-IV Idea Group grants +1 Era Momentum per month, capped at +2 from idea groups;
- the first completion of each objective in the current age grants +50 once;
- losing the condition stops monthly income but never allows the +50 to trigger again in that age.

The ledger separates the two readings: **currently met** objectives are evaluated live, while **secured this Age** counts the one-time completion flags used for Golden Age eligibility. The persistent count is reconciled from those flags each monthly tick, so older saves and delayed initialization cannot leave the ledger at an incorrect value.

### 8.3 Era rewards

Reward costs escalate within each age:

| Purchase number | Cost |
| ---: | ---: |
| 1 | 200 |
| 2 | 300 |
| 3 | 400 |
| 4 | 500 |
| 5+ | 600 |

The ladder resets at the next age. Reward modifiers last only for their age.

Shared reward slots:

| Slot | Age 1 | Age 2 | Age 3 |
| ---: | --- | --- | --- |
| 1 | +50 Bureaucracy | +5% Education Access | +1 Social Security max investment |
| 2 | +5% Education Access | -3% Mortality | +5 Legitimacy |
| 3 | +5% Law Enactment Success | +10% Tax Capacity | +5 Weekly Innovation |
| 4 | -5% Loan Interest | +15% Resource Discovery | +10% Infrastructure |
| 5 | +5% Manufacturing Throughput | +5% Manufacturing Throughput | +10% Manufacturing Throughput |
| 6 | +5% Infrastructure | +10% Trade Advantage | -5% Military Goods Cost |
| 7 | +5% Influence | +10% Colony Growth | -10% casualty War Exhaustion |
| 8 | +10% Ship Supply Capacity | +10% Influence | +10% Army Movement Speed |
| 9 | +5% Army Offense | +10% Conscription Rate | +15% Improve Relations Speed |

Restricted slots:

| Age | Slot 10 | Slot 11 | Slot 12 | Slot 13 |
| --- | --- | --- | --- | --- |
| Age 1 | Italian primary culture: -25% conquest radicals | German primary culture: +15% Infamy Decay | NET: +15% Trade Advantage | TUR: +1 maximum law setback |
| Age 2 | AUS: -1.5% in three hostility radical channels | RUS: +35% Assimilation | BEL: +20% Colony Growth | USA: +10% Minting |
| Age 3 | GBR: naval-invasion package, with a Naval-idea-dependent alternate | CHI: +10 Weekly Innovation | FRA: +15% defense in owned provinces | JAP: +15% Ship Supply Capacity |

### 8.4 Golden Ages

From 1845 onward, completing five distinct objectives in an age enables a Golden Age. A country may activate only one Golden Age during the entire campaign. Duration is 15 years. The selection tooltip reports the one-per-campaign lock, year gate, and objective gate separately.

| Type | Effects |
| --- | --- |
| Industrial | +10% Manufacturing Throughput, +10% Resource Discovery Chance |
| Cultural | +5% Education Access, +10% Prestige |
| Strategic | +5% Army Offense, -10% casualty War Exhaustion |

### 8.5 Era Crossroads rollout

Phase 6 adds one strategic Crossroads Journey per Age. Its offer carrier runs
93 days after the country half-yearly pulse. Age 1/2/3 offer windows close at
1866/1901/1932 respectively, and each Age can be offered only once.

The common contract is:

- one pending offer reservation for 14 days;
- three route options and one decline option per Age offer;
- at most one active Crossroads per country;
- one Age-specific Journal Entry shell with 0–60 progress and a 1,825-day timeout;
- monthly progress of +0/+1/+2 according to two route anchors;
- the active Journey invalidates without reward when its Age ceases to be current;
- successful completion grants exactly +50 Era Momentum and does not mutate
  objective completion/count, Golden Age state, or Era Reward purchase state.

Age 1 **Steam and the State** is live. Its route contracts are:

| Route | Secured objective flags read | Route-fit Idea IV |
| --- | --- | --- |
| Steam Network | Age 1 objectives 1 and 5 | Industrialist or Infrastructure |
| Educated Citizenship | Age 1 objectives 2 and 4 | Academic or Reformist |
| Administrative State | Age 1 objectives 3 and 6 | Bureaucratic or Parliamentary |

The route selection AI favors already secured anchors and receives a smaller
boost from route-fit doctrine. Decline gains weight only when no Age 1 route
has a secured anchor or doctrine fit.

At 20 and 40 progress, Age 1 fires **A National Calendar** and **Who Will
Direct Progress?**. Each has exactly three choices: spend 10 National Insight
for +3 progress, take a free neutral option, or—when the selected route has a
matching level-IV Idea Group—spend 5 National Insight for +3 progress. Paid
options repeat affordability and active-context checks inside their hidden
effects. Insight uses the shared 0–1000 clamp.

Age 2 **Empire and Mass Society** is also live:

| Route | Secured objective flags read | Route-fit Idea IV |
| --- | --- | --- |
| Imperial Horizon | Age 2 objectives 3 and 4 | Diplomatic or Colonial |
| Mass Welfare | Age 2 objectives 2 and 6 | Welfare or Reformist |
| Integrated Nation | Age 2 objectives 1 and 5 | Nationalist or Labour |

Its route AI uses the same secured-anchor and doctrine-fit weighting contract.
At 20 and 40 progress it fires **The Reach of the State** and **The Price of
Integration**, using the same 10-Insight paid, free neutral, and 5-Insight
route-doctrine option budget. Completion reports the shared +50 Momentum
reward through the Age 2 closure event.

Age 3 **The Mobilized Society** is live:

| Route | Secured objective flags read | Route-fit Idea IV |
| --- | --- | --- |
| Social Republic | Age 3 objectives 1 and 2 | Parliamentary or Welfare |
| Strategic Command | Age 3 objectives 5 and 7 | Professional Army or Defensive |
| Arsenal Society | Age 3 objectives 3 and 6 | War Economy or Mass Conscription |

At 20 and 40 progress it fires **The Nation Is Called to Duty** and **A
Permanent Emergency**, with the same milestone resource budget and safety
checks as the first two Ages. War entry, victories, casualties, and conquest
are not route anchors or alternate progress sources. Completion reports the
shared +50 Momentum reward through the Age 3 closure event.

All three `ve_era_crossroads_age_N_pack_live` triggers now return
`always = yes`. No dormant milestone branch remains.

Phase 6 static acceptance is complete at **20/20**. The verified implementation
contains 12 unique events, three Journal Entries, nine routes with 18
read-only objective anchors, six milestones, three closure events, matching
106-key English/Turkish localization sets, and 21 valid vanilla asset
references. Crossroads content has no mutation path into objective/Golden Age,
Era Reward purchase, Project, Settlement, Cohesion, National Idea, capacity,
or Strain state. Runtime distribution and pacing observations remain deferred
by user decision.

Primary sources:

- `common/scripted_triggers/ve_age_triggers.txt`
- `common/script_values/ve_age_values.txt`
- `common/scripted_effects/ve_age_effects.txt`
- `common/on_actions/ve_era_crossroads_on_actions.txt`
- `common/scripted_triggers/ve_era_crossroads_triggers.txt`
- `common/script_values/ve_era_crossroads_values.txt`
- `common/scripted_effects/ve_era_crossroads_effects.txt`
- `common/journal_entries/ve_era_crossroads_journal_entries.txt`
- `common/static_modifiers/ve_age.txt`
- `common/scripted_guis/ve_ages.txt`
- `common/scripted_guis/ve_era_momentum.txt`
- `events/developer_events.txt`
- `events/ve_age_events.txt`
- `events/ve_era_crossroads_events.txt`
- `gui/ve_panel_age_bonusses.gui`
- `localization/english/ve_age_l_english.yml`
- `localization/english/ve_era_crossroads_l_english.yml`
- `localization/english/ve_modifiers_l_english.yml`
- `localization/turkish/ve_era_crossroads_l_turkish.yml`

### 8.6 Tag Flavor rollout

Phase 7 has a shared country tag-flavor carrier. It runs 45 days after the
yearly country pulse. The child on-action can roll only when at
least one pilot passes its tag, National Idea profile, date, feature-context,
one-off, and shared lifecycle gates. Its single frequency roll is 25%.

The shared lifecycle contract is:

- `ve_tag_flavor_offer_pending` and `ve_tag_flavor_offer_chain`: 14 days;
- `ve_tag_flavor_active_chain` and `ve_tag_flavor_route`: 450 days;
- pilot closure timing: exactly 365 days from the opener route choice;
- country-scoped `ve_tag_flavor_cooldown`: 2,920 days after completion;
- one persistent offered and completed flag per pilot;
- deterministic dispatcher priority TUR, then JAP, then USA;
- closure context requires the same country tag, National Idea profile, active
  chain, and route 1–3.

The TUR, JAP, and USA pack-live triggers all return `always = yes`.

The live TUR chain is **The Language of Reform**:

- requires TUR, `tur_idea_2`, 1840–1895, initialized Religious and Identity
  models, and no active Religious or Identity Transition Journey;
- **A Common Civic Lexicon** requires Civic Nation or Composite State and
  spends 20 Cultural Mandate; after 365 days it grants +8 National Insight,
  +3 National Cohesion, and 24 months of +1% Education Access / -25 Authority;
- **Sacred Continuity** requires the synchronized Confessional model/law and
  spends 20 Piety Reform; after 365 days it grants +8 National Insight,
  +3 Religious Settlement, and 24 months of +25 Authority / -2.5% Technology
  Spread;
- **Administrative Translation** is the always-available free fallback; after
  365 days it grants +4 National Insight and 24 months of +25 Bureaucracy /
  -2.5% Law Enactment Speed.

Paid choices repeat their fit, affordability, and active-offer context in the
visible option, hidden effect, and begin helper. Closure reads only the stored
route plus the original TUR/National Idea profile context; a later model change
does not reinterpret the historical choice. Completion marks the TUR pilot
complete, applies the shared 2,920-day cooldown, and clears the session.

The live JAP chain is **Borrowed Methods, Native Authority**:

- requires JAP, `jap_idea_2`, 1850–1910, and an initialized current Age;
- **Translation Bureaus** requires Academic Idea IV or Infrastructure Idea IV
  and spends 15 National Insight; after 365 days it grants +10 Era Momentum
  and 24 months of +2.5% Technology Spread / -25 Authority;
- **Directed Borrowing** requires `jap_idea_4` and spends 10 National Insight;
  after 365 days it grants +7 Era Momentum and 24 months of +25 Authority /
  -2.5% Law Enactment Speed;
- **Selective Adoption** is the free fallback; after 365 days it grants +3 Era
  Momentum and 24 months of +25 Authority / -2.5% Technology Spread.

JAP uses the same triple fit/affordability/context check and delayed closure
safety as TUR. Era Momentum changes only `ve_splender_points` through its
actual-delta helper and zero floor. The chain does not research technology,
complete objectives, activate a Golden Age, or purchase an Era Reward.

The live USA chain is **The Meaning of the Union**:

- requires USA, `usa_idea_1`, 1845–1905, an initialized Identity Model, and no
  active Identity Transition Journey;
- **Citizenship Compact** requires Civic Nation and spends 20 Cultural
  Mandate; after 365 days it grants +8 National Insight, +3 National Cohesion,
  and 24 months of +2.5% Migration Attraction / -25 Authority;
- **Composite Bargain** requires Composite State and spends 20 Cultural
  Mandate; after 365 days it grants +8 National Insight, +3 National Cohesion,
  and 24 months of +25 Bureaucracy / -2.5% Assimilation;
- **Federal Ambiguity** is the free fallback; after 365 days it grants +4
  National Insight and 24 months of +25 Influence while applying -2 to the
  National Cohesion equilibrium.

The Federal Ambiguity pressure is read by `ve_common_national_cohesion`; it
does not subtract Cohesion directly and disappears with the modifier. The USA
chain does not change citizenship laws, add accepted/constituent cultures,
create pop conversion/assimilation effects, or mutate Cultural Project state.

Phase 7 static acceptance is complete at **20/20**. The verified package
contains three live pilots, six unique events, nine routes, nine 365-day
closure schedules, nine 24-month modifiers, and matching 56-key English and
Turkish localization sets. All 61 custom references, 12 event calls, eight
vanilla modifier types, and eight vanilla assets resolve. No mutation path was
found into National Idea progression/capacity, Religious or Identity Models,
laws, Project lifecycle, objectives, Golden Ages, Era Reward purchases,
technology, buildings, pops, culture/religion conversion, or war outcomes.
Runtime distribution and save/load observations remain deferred by user
decision and do not block the static closure.

Shared resource helpers account for the actual post-clamp delta of National
Insight (0–1000), Cultural Mandate and Piety Reform (0–500), National Cohesion
and Religious Settlement (0–100), and Era Momentum (zero floor). They write
only feature-prefixed telemetry totals and do not mutate National Idea level or
pool, Idea Group capacity, models/laws, Project lifecycle, objective/Golden Age
state, or Era Reward purchases.

Primary sources:

- `common/on_actions/ve_code_on_actions.txt`
- `common/on_actions/ve_tag_flavor_on_actions.txt`
- `common/scripted_triggers/ve_tag_flavor_triggers.txt`
- `common/scripted_effects/ve_tag_flavor_effects.txt`
- `common/script_values/ve_national_identity_values.txt`
- `common/static_modifiers/ve_tag_flavor_modifiers.txt`
- `events/ve_tag_flavor_events.txt`
- `localization/english/ve_tag_flavor_l_english.yml`
- `localization/turkish/ve_tag_flavor_l_turkish.yml`
- `PHASE_7_TAG_FLAVOR_CONTENT_BIBLE_TR.md`

## 9. GUI, alerts, and AI

Main VE UI:

- shell: `gui/ve_gui_panel.gui`;
- Ideas: `gui/ve_panel_ideas.gui`;
- Religion: `gui/ve_panel_religion.gui`;
- National Identity: `gui/ve_panel_culture.gui`;
- Era: `gui/ve_panel_age_bonusses.gui`;
- country panel doctrine readout: `gui/ve_country_panel_doctrines.gui` (see 9.1).

### 9.0 Topbar resource row

`gui/topbar.gui` adds a third topbar row that the small round button at the end of the vanilla secondary row toggles against the mod's "extra info" row (`ve_top_bar` scripted GUI). The VE row is drawn only for an initialized country (`ve_show_ve_topbar_row`); otherwise the extra-info row is shown so the third row is never blank.

Every entry is a `ve_topbar_chip` — a `glow_button` carrying a vanilla icon, a short value, a tooltip, and a click that opens the owning panel tab through `ve_tab_var`. Order is by system:

| Chip | Value | Icon | Tooltip | Click |
| --- | --- | --- | --- | --- |
| National Insight | `idea_point_pool` | `generic_icons/innovation` | `ve_tb_insight_tt` | Ideas |
| Idea Groups | `idea_group_unlocked`/`idea_group_cap` | `institution_icons/schools` | `ve_tb_idea_groups_tt` | Ideas |
| Piety Reform | `piety_reform_point` | `central_identity_pillars_icons/religious` | `ve_tb_piety_reform_tt` | Religion |
| Religious Settlement | `piety_bar_point` | `generic_icons/conversion` | `ve_tb_settlement_tt` | Religion |
| Religious Project | `ve_religious_project_progress`%, only while active | `generic_icons/national_awakening` | `ve_tb_religious_project_tt` | Religion |
| Cultural Mandate | `culture_reform_point` | `generic_icons/mandate` | `ve_tb_mandate_tt` | National Identity |
| National Cohesion | `ve_national_cohesion` | `generic_icons/cohesion` | `ve_tb_cohesion_tt` | National Identity |
| Cultural Project | `ve_cultural_project_progress`%, only while active | `generic_icons/cultural_fervor` | `ve_tb_cultural_project_tt` | National Identity |
| Era Momentum | `ve_splender_points` | `generic_icons/age` | `ve_tb_momentum_tt` | Era |

Rules that must hold when this row is edited:

- Chips are 60–74 wide, so the value text is a bare number. Caps, breakdowns and rules belong in the tooltip.
- Each `ve_tb_*_tt` key nests the matching full panel tooltip (`$ve_piety_tt$`, `$ve_national_insight_tt$`, …) plus a click hint, so a change to a panel tooltip reaches the topbar automatically.
- Piety Reform is **not** gated on `ve_religious_project_enabled`. It is earned and spent under every Religious Model, including Total Separation; only starting a project is gated.
- The old EU4-style mod textures (`gfx/interface/icon_ideas.dds`, `catholic.dds`, `monarch_cultures_icon.dds`, `icon_splendor_tiny.dds`, `icon_envoy_missionary.dds`) are no longer used by the topbar.
- Visibility bindings live in `common/scripted_guis/ve_topbar.txt`; the project chips additionally require the progress variable, which is removed on completion or cancellation.
- Superseded keys `religious_project_topbar`, `piety_topbar`, `cultural_reform_topbar`, `idea_point_topbar`, `splendor_topbar` and their `*_tt` variants are no longer referenced by English; other language files still define them.

### 9.1 Country panel doctrine readout

The Information tab of the country panel carries a read-only doctrine section for **any** country, the player's own and foreign ones alike. It never exposes a purchase, start, or cancel action; those stay in the fullscreen panels.

Contents, in order:

1. resource strip: National Insight, Piety Reform, Cultural Mandate, Era Momentum, each with its stock bar;
2. Ideas: idea-group slots used/available, the seven National Idea slots plus Tradition and National Bonus chips, National Idea progress out of 21, and one row per embraced idea group with seven purchase pips and the Ambition marker;
3. Religion: Religious Model, Religious Settlement meter with its tier, the eight Religious Program slots, and Religious Project status/progress;
4. National Identity: Identity Model, National Cohesion meter with its tier, and Cultural Project status/progress;
5. Era: current Age, Era Momentum, objectives completed out of 7, Golden Age status, and the thirteen Era Reward slots.

Layout rules that must hold when this section is edited: the section is 554 wide, cards are clamped to 530 and rows to a fixed height, long names are elided instead of wrapped, and per-slot detail lives in tooltips. Group rows for groups a country never embraced are hidden, so the list cannot exceed seven rows. The whole section collapses through the `ve_cp_collapsed` GUI variable on the header arrow.

Hard structural constraint: `country_panel_information_content` is a `flowcontainer`, and a `(flow)container` cannot have an `hbox`/`vbox` as a direct child — doing so crashes the game with `EXCEPTION_STACK_OVERFLOW` during layout. Therefore every vertical stack in this section is a `flowcontainer` and every horizontal row is a fixed-size `widget` that hosts its own `hbox`, mirroring vanilla `attitude_info`. Also note that a plain `widget` does not accept `margin = { x y }`; use `margin_left`/`margin_right`/`margin_top`/`margin_bottom` on containers instead.

Tooltips in this section must be country-scoped. The pre-existing `ve_piety_tt`, `ve_national_cohesion_tt`, and `ve_religious_project_progress_tt` keys read `GetPlayer` and would show the player's own numbers on a foreign country's panel, so this section uses its own `VE_CP_*` tooltip keys. Project progress variables are removed while no project runs, so those lines are reachable only through the active branch of `ve_cp_religious_project_detail` / `ve_cp_cultural_project_detail`.

Sources:

- `gui/ve_country_panel_doctrines.gui` (types), `gui/country_panel.gui` (single insertion in `country_panel_information_content`)
- `common/scripted_guis/ve_country_panel.txt`
- `common/scripted_triggers/ve_country_panel_triggers.txt`
- `common/customizable_localization/ve_country_panel_cl.txt`
- `localization/english/ve_country_panel_l_english.yml`, `localization/turkish/ve_country_panel_l_turkish.yml`

Alerts/important actions cover:

- an affordable next group idea;
- an affordable Religious Program;
- excess Cultural Mandate with an available project;
- an affordable Era reward;
- an eligible state for a Targeted Cultural Project;
- an eligible state for a Targeted Religious Project.

AI behavior:

- monthly: progress the current idea focus if affordable;
- half-yearly: refresh/choose idea-group focus, buy religious programs, choose identity changes and projects, and select era rewards/Golden Age;
- targeted projects: sort eligible states by population and choose the largest.

Sources:

- `common/alert_types/ve_alert_types.txt`
- `common/alert_groups/ve_alert_groups.txt`
- `common/scripted_effects/ve_ai_effects.txt`
- `common/scripted_guis/ve_topbar.txt`
- `gui/topbar.gui`

### 9.2 Religion and National Identity pages

Both pages share one layout contract. Keep them symmetric when either changes:

1. A card shows an icon, a name and at most one short line. The full modifier list lives in that card's tooltip (`*_desc` / `*_tt`).
2. Current state is stated twice: in the summary strip, and on the card as a checkmark plus a footer label that replaces the action button.
3. Each meter is `value / max`, a signed monthly delta from its script value, a progress bar, and an optional status line - a tier badge at the 75+/25- bands, a project target, or a live blocking timer.
4. A blocking timer is never silent: an active strain or backlash prints a red notice both next to the meter it caps and in the section label it blocks.

Neither page scrolls, and neither uses tabs. Each is one screen: a summary strip, then one row per section, every row packed horizontally so its height is fixed. Rules that keep it that way:

- A section is one label line plus an information icon; the icon's tooltip is that section's help paragraph. Nothing explanatory is printed on the page - only conditional red notices (strain, backlash), and only while they are live.
- A full-width row must not cluster its content on the left with a dead gap in the middle. Split it into `layoutpolicy_horizontal = expanding` columns separated by vanilla `vertical_divider` (`blockoverride "size" { size = { 16 100% } }`), and centre the action cluster with the same expand-wrapped vbox used for icons. Both project rows follow this.
- A fixed-width control inside an expanding card floats in the frame and looks unfinished. Give the action `layoutpolicy_horizontal = expanding` with `size = { 0 h }` (the vanilla pattern) so it hugs the card margins at every resolution, and keep the button label to one verb - costs and conditions belong on their own line or in the tooltip.
- Never give a box child `parentanchor`. An anchored child is positioned by the anchor instead of flowing, so its parent reserves no room for it and it spills out of the `main_bg` plate - this is what pushed every leading icon outside its card on 2026-07-29. To centre an icon in a row, wrap it in `vbox = { layoutpolicy_vertical = expanding  expand = {} <icon> expand = {} }`; mutually exclusive icon variants share one wrapper, since a hidden child takes no height and the row then pays its spacing once.
- Cards in a row must be equalised, or a longer body overflows its `main_bg` plate while its neighbours stay short. Give every card in the row `layoutpolicy_vertical = expanding`, a `minimumsize` height that fits the tallest body (identity 146, religion model 116, culture project 132), and an `expand = {}` above the cost/action pair so the actions land on the bottom margin and line up. Card bodies are authored to wrap to a fixed number of lines - if a string grows, the cap and the minimum height both have to grow with it.
- Width first, then height. A card in a four-across row has ~250 px of body at 1366 and one in a three-across row ~330 px; a `maximumsize` wider than that clips at the card edge instead of wrapping. Set the width to the real column, then give the height the number of lines the string actually wraps to (a two-line body needs ~36 px, a three-line one ~50).
- No widget may grow vertically with its content. Long text is `elide = right` or capped by `maximumsize = { w h }`; one uncapped multiline textbox brings the scrollbar back.
- Where a row has no width for a full sentence, the page uses a `*_short` localization variant and keeps the long form in the tooltip (`ve_adopt_program_button_short`, `ve_switch_identity_button_short`, `ve_*_backlash_notice_short`, `ve_*_start_instruction_short`).
- Strings the page stopped printing were folded into the tooltip that replaced them with `$key$` nesting (the five meter hints, both project start instructions), so no information was dropped.

Budget at 1366x768, where the fullscreen content area is about 630 px: Religion needs ~580 (strip 100, models 90, eight program cards in one row 150, project 110, three section labels and spacing ~130) and National Identity ~470.

Page composition:

| Section | Religion (`ve_panel_religion.gui`) | National Identity (`ve_panel_culture.gui`) |
| --- | --- | --- |
| Summary strip | state religion, model name, and meters for Settlement, Piety Reform, Religious Project | primary cultures, Identity Model, and meters for Cultural Mandate, National Cohesion, Cultural Project |
| Model section | four models, read-only - the model follows the Church and State law | three models, each with a cost line and a full-width `Switch` button (`ve_choose_*_identity`) |
| Middle section | eight Programs in one row (`ve_religion_program_card` type, one `ve_aspect_button_N` each). Card contents stretch with the frame: `layoutpolicy_horizontal = expanding` action, cost on its own line, `Adopt` as the only button word | - |
| Project section | one wide card: the running project with a country-scope cancel + confirm, or the model's project and how to start it from a state | same shape when one runs; otherwise the two countrywide projects and the model project side by side |

Religion page bindings added on 2026-07-29:

- `ve_has_active_religious_project_gui`, `ve_has_no_active_religious_project_gui`, `ve_cancel_religious_project_gui`, `ve_religious_program_strain_gui`, `ve_religious_project_backlash_gui` in `common/scripted_guis/ve_religious_state.txt`; `ve_identity_transition_backlash_gui` and `ve_cultural_project_backlash_gui` on the identity side.
- `ve_religious_project_type_is = { TYPE = n }` (1 Confessional Conversion, 2 Freedom Outreach, 3 Secularization Campaign).
- `ve_religious_project_name` / `_description` / `_target` and `ve_religion_model_project_name` / `_cost` / `_short` / `_description`, mirroring the cultural set; `ve_identity_high_cohesion_effect` mirrors `ve_religious_high_settlement_effect`.
- Per-card "hover for details" lines, per-section help paragraphs and the per-section `header_pattern` headers were removed on 2026-07-29 for vertical space; the tab row replaced the headers and carries the help text. Fixed sizes were reduced in the same pass (strip icons 84 -> 64, card icons 64 -> 48 and 56 -> 44, program texticons 45 -> 36, buttons 300/260x40 -> 260/240x32, bars 150x12 -> 140x10).
- The old round `button_icon_round_big_map_interaction` program grid, and its duplicated shown/not-shown label pair, are gone.

### 9.3 Doctrine Ledger

The fifth tab of the mod panel (`ve_tab_var = ve_ledger`) is a sortable, filterable, paged table of every country's doctrine state: rank, National Insight, embraced idea groups, purchased group ideas with the seven National Idea markers, Religious Model with Settlement, Identity Model with Cohesion, and Era standing. It is read-only, and the player's own country is pinned above the page as the comparison baseline. Clicking a country closes the panel and opens that country's panel, whose National Doctrine section (9.1) carries the per-group detail.

Engine constraints that shaped the design:

- The GUI cannot sort or filter a data model, and it cannot read text typed into an `editbox`. **Free-text country search is therefore impossible**; the ledger replaces it with sorting, filters and the paging controls.
- Sorting and filtering happen in script. `ve_ledger_rebuild` keeps one global list, `ve_ledger_countries`, that always holds exactly the rows of the page on screen, in order. Row *values* are read live off the country, so only the ordering and page membership are as old as the last rebuild.
- The rebuild picks rows with repeated `ordered_country ... position = 0` passes, marking each taken country with `ve_ledger_taken` (always cleared again at both ends of the rebuild). One pass consumes the rows before the page, one collects the page.
- Paging exists for performance: 20 rows keep the per-frame scripted-GUI evaluations bounded, and a rebuild only walks the country list `offset + 20` times.

Presentation state, all global variables: `ve_ledger_sort` (1 prestige, 2 Insight, 3 group ideas, 4 groups, 5 Settlement, 6 Cohesion, 7 Momentum, 8 Era Rewards), `ve_ledger_filter` (0 all, 1 great powers, 2 major or better, 3 recognized, 4 diplomatically relevant to the viewer, 5 has an idea group), `ve_ledger_offset`, `ve_ledger_total`, `ve_ledger_page_number`, `ve_ledger_page_count`. The rebuild and every filter run with the viewing player's country as ROOT, which is what lets filter 4 be "relative to me".

The table uses absolute column offsets (`@ve_lg_*` in the GUI file) instead of a box layout, because header and rows must align to the pixel and because box children may not carry a position - see the structural rules in 9.1.

Sources:

- `gui/ve_panel_ledger.gui`, tab wiring in `gui/ve_gui_panel.gui`
- `common/scripted_guis/ve_ledger.txt`
- `common/scripted_effects/ve_ledger_effects.txt`
- `common/scripted_triggers/ve_ledger_triggers.txt`
- `common/script_values/ve_ledger_values.txt`
- `localization/english/ve_ledger_l_english.yml`, `localization/turkish/ve_ledger_l_turkish.yml`

## 10. Naming, compatibility, and stale-reference notes

- `ve_splender_points` and `splender_points_value` are misspelled but stable save/script identifiers. Do not rename them without a migration.
- `piety_bar_point` is the Religious Settlement meter in the active design, not spendable Piety.
- `culture_reform_point` is Cultural Mandate in the active design.
- Religion customizable-localization keys were normalized to the `ve_` prefix on 2026-07-29: `religion_aspect_N` -> `ve_religion_aspect_N`, `religion_aspect_text_N` -> `ve_religion_program_name_N`, `religion_aspect_9` -> `ve_religion_model_icon`. The texticon names they resolve to (`catholic_aspect_N`, `protestant_aspect_N`, `separation_aspect_N`, `atheist_aspect_N`) are unchanged.
- Turkish covers the Religion page labels and tooltips but not the model, program, or project card text on either page; the National Identity page has almost no Turkish. English is the complete set.
- The old missionary system is retired. New religion work belongs in `ve_religious_project_*`.
- The old ±7 culture reform bar is retired. New culture work belongs in National Identity/Cultural Projects.
- The live idea system contains 21 groups, including Agrarian.
- National Idea progress comes from purchased individual group-idea levels, not completed-group count.
- Idea-group capacity no longer opens every ten years. It is earned permanently at 4/8/13/19/26/34 current purchased group-idea levels, with Age 2 gates on slots 5–6 and an Age 3 gate on slot 7.
- Doctrine Implementation Strain blocks another group-idea purchase for its full 24-month duration as well as reducing National Insight income.
- `IDEA_GROUP_BALANCE.md` does not fully reflect the previous two live rules.
- `events/Economic_Idea.txt` and `events/InnovativeIdeaGroupEvents.txt` (13 flavor events) are not dispatched from any `on_action` or effect, and every event in a file shares one localization key set (`economic_flavor.1.*` / `innovative_flavor.1.*`). The shared keys now exist so the load no longer errors; wiring the events up requires per-event keys and a deliberate hook.

## 11. Update checklist

When changing any documented mechanic, verify:

1. Are variables, trigger/effect identifiers, modifier IDs, thresholds, and localization keys still accurate here?
2. Did monthly, half-yearly, yearly, law-change, formation, or state-owner dispatch change?
3. Did state-panel visibility, affordability, target selection, progress, completion, or cancellation change?
4. Does AI use the same eligibility and cost rules as the player?
5. Do alerts match actions the player can actually take?
6. Does the change need a save migration or compatibility bridge?
7. Was `MECHANICS_REFERENCE.md` updated in the same task?
