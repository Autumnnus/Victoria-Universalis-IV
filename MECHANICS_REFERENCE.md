# Victoria Universalis IV — Mechanics Reference

This is the durable, AI-oriented reference for the mod's active mechanics. Read it before answering, designing, debugging, or implementing work involving religion, National Identity/culture, Cultural or Religious Projects, idea groups, National Ideas, ages/Era Momentum, or the culture and religion actions in the state panel.

Last verified against the implementation: **2026-07-29**

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
| Monthly | `ve_monthly_country_tick` | Update Religious Settlement, Piety Reform, Religious Project, National Insight, Cultural Mandate, National Cohesion, Cultural Project, Era Momentum, and objective completion. AI tries to buy the next idea in its current focus. |
| Half-yearly | `ve_half_yearly_country_tick` | AI chooses idea groups, religious programs/projects, identity/cultural projects, era rewards, and Golden Ages. |
| Yearly | `ve_yearly_country_tick` | Update the year-based idea-group capacity. Hidden age-transition events are also checked yearly. |
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
| `law_state_religion` and variants | Confessional State | 1 | +5% Authority, +10% Conversion, +10% Devout political strength, -3% Migration Attraction, +5% radicals from Open Prejudice |
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

Known discrepancy: the live affordability trigger requires **25 Piety Reform**, while some English tooltips still say “at least 50.” Treat 25 as the implemented behavior until code or localization is deliberately changed.

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
- radical religious movements, low Settlement, and target-state turmoil reduce progress.

Completion:

| Project | Outcome |
| --- | --- |
| Confessional Conversion | Convert 5% of the target state's population to the country's state religion, add small radicals, refund 20 Piety Reform, add 5 Settlement |
| Freedom Outreach | No forced conversion; add state loyalists, refund 20 Piety Reform, add 7 Settlement |
| Secularization Campaign | Convert 5% to `rel:atheist`, add small radicals, refund 25 Piety Reform, add 8 Settlement |

Nationalist group ideas 2, 5, and 7 each add 3 percentage points to conversion projects, for up to +9 percentage points. The total converted share is the state-scope script value `ve_religious_project_conversion_amount` (5% base plus the owner's bonuses) in `common/script_values/ve_religious_project_values.txt`. It used to live in the effects file as `ve_religious_conversion_bonus`, where the parser rejected it, so no bonus was ever applied.

Normal cancellation:

- no Piety Reform refund;
- -5 Religious Settlement;
- 24-month backlash: -50 Bureaucracy, -50 Authority, -3% Law Enactment Success.

Primary sources:

- `common/scripted_triggers/ve_religious_state_triggers.txt`
- `common/script_values/ve_religious_state_values.txt`
- `common/script_values/ve_religious_project_values.txt`
- `common/scripted_effects/ve_religious_state_effects.txt`
- `common/scripted_guis/ve_religious_state.txt`
- `common/customizable_localization/ve_religious_state_cl.txt`
- `common/static_modifiers/ve_religious_state.txt`
- `gui/ve_panel_religion.gui`
- `localization/english/ve_religion_l_english.yml`

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
- an active project applies -75 Bureaucracy and -25 Authority;
- progress runs from 0 to 100 and monthly progress is clamped to 1–7;
- administration, legitimacy, model/society fit, and high Cohesion help progress;
- radical cultural movements and target-state turmoil slow progress;
- normal cancellation gives no refund, removes 5 Cohesion, and applies a 24-month backlash;
- backlash applies -50 Bureaucracy, -25 Authority, and -3% Law Enactment Success.

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
| Ethnic | Ethnic Integration Campaign | 125 Mandate | Convert 5% of target culture pops to the stored primary culture; +25 Mandate, +8 Cohesion, radicals, and a 10-year assimilation result |
| Civic | Equal Citizenship Initiative | 100 Mandate | +15 Acceptance for 10 years, state loyalists, +25 Mandate, +10 Cohesion, and a 10-year qualifications/migration result |
| Composite | Constituent Compact | 150 Mandate and at least 40 Cohesion | Permanent +15 Acceptance, add culture to the constituent list, state loyalists, +30 Mandate, +12 Cohesion |

Primary sources:

- `common/scripted_effects/ve_national_identity_effects.txt`
- `common/scripted_triggers/ve_national_identity_triggers.txt`
- `common/script_values/ve_national_identity_values.txt`
- `common/scripted_effects/ve_cultural_project_effects.txt`
- `common/scripted_triggers/ve_cultural_project_triggers.txt`
- `common/script_values/ve_cultural_project_values.txt`
- `common/static_modifiers/ve_national_identity.txt`
- `common/static_modifiers/ve_cultural_projects.txt`
- `common/scripted_guis/ve_national_identity.txt`
- `common/scripted_guis/ve_cultural_projects.txt`
- `common/customizable_localization/ve_national_identity_cl.txt`
- `common/customizable_localization/ve_cultural_projects_cl.txt`
- `gui/ve_panel_culture.gui`
- `localization/english/ve_culture_l_english.yml`

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

A completed group costs 2800 total Insight. Every level purchase applies 24 months of Doctrine Implementation Strain.

### 6.2 Group capacity

Countries start with one group slot. The yearly update raises capacity:

| Year | Capacity |
| ---: | ---: |
| 1836 | 1 |
| 1846 | 2 |
| 1856 | 3 |
| 1866 | 4 |
| 1876 | 5 |
| 1886 | 6 |
| 1896 | 7 |

Embracing a group costs no Insight. It occupies one slot and enables purchases in that group.

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

### 6.4 Age gates and mutually exclusive paths

Locked until Age 2:

- Labour;
- Welfare;
- Nationalist;
- Reformist;
- Mass Conscription;
- Colonial.

Locked until Age 3:

- War Economy.

Extraction can be embraced in Age 1, but its seventh level cannot be purchased until Age 3.

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
- Group count and National Idea progress are recalculated; falling below a National Idea threshold may revoke that National Idea.

Exact group modifiers: `common/static_modifiers/ve_group_ideas.txt`.

Primary sources:

- `common/script_values/ve_script_values.txt`
- `common/scripted_effects/ve_idea_effects.txt`
- `common/scripted_effects/ve_scripted_effects.txt`
- `common/scripted_guis/ve_idea.txt`
- `gui/ve_panel_ideas.gui`
- `localization/english/ve_idea_l_english.yml`
- `localization/english/ve_modifiers_l_english.yml`

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
- the first completion of each objective in the current age grants +50 once;
- losing the condition stops monthly income but never allows the +50 to trigger again in that age.

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

Primary sources:

- `common/scripted_triggers/ve_age_triggers.txt`
- `common/script_values/ve_age_values.txt`
- `common/scripted_effects/ve_age_effects.txt`
- `common/static_modifiers/ve_age.txt`
- `common/scripted_guis/ve_ages.txt`
- `common/scripted_guis/ve_era_momentum.txt`
- `events/developer_events.txt`
- `events/ve_age_events.txt`
- `gui/ve_panel_age_bonusses.gui`
- `localization/english/ve_age_l_english.yml`
- `localization/english/ve_modifiers_l_english.yml`

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

### 9.2 Doctrine Ledger

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
- The old missionary system is retired. New religion work belongs in `ve_religious_project_*`.
- The old ±7 culture reform bar is retired. New culture work belongs in National Identity/Cultural Projects.
- The live idea system contains 21 groups, including Agrarian.
- National Idea progress comes from purchased individual group-idea levels, not completed-group count.
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
