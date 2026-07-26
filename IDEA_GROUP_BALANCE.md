# Idea Group Balance Specification

This document is the design reference for group identities and balance. The
modifier definitions remain manually maintained in
`common/static_modifiers/ve_group_ideas.txt`.

## System rules

- The game should normally support four to five completed groups, with six
  representing a long and successful campaign.
- One completed group grants three `national_idea_pool` points. National ideas
  unlock at 3/6/9/.../21, so partial groups do not advance national ideas.
- Idea costs remain 200/250/300/375/450/550/675 (2800 total).
- Nationalist/Reformist and Professional Army/Mass Conscription are mutually
  exclusive for both players and AI.
- Age 2 gates Labour, Welfare, Nationalist, Reformist, Mass Conscription, and
  Colonial. Age 3 gates War Economy and Extraction idea 7 (oil).
- Cancelling a group refunds no idea points. It removes that group's national
  progress and may revoke national modifiers whose thresholds are no longer met.

## Modifier power bands

High-leverage modifiers affect the whole economic, political, demographic, or
military loop. Repetition across an idea, capstone, and ambition must be counted
as one combined total.

| Band | Examples | Typical normal idea | Typical completed-group total |
| --- | --- | ---: | ---: |
| High | construction, working adult ratio, infamy, mortality, law enactment, army offense/defense | 2–5% | 10–20% |
| Medium | bureaucracy, authority, influence, infrastructure, qualifications, migration | 5–10% | 20–30% |
| Narrow | one building group, one good, terrain, ports, convoys, colony specialization | 10–15% | 20–40% |

Flat values use their vanilla scale and must be compared with current technology,
laws, traits, and power-bloc bonuses rather than percentage bands.

## Group identity matrix

| Category | Group | Intended user | Primary strength | Supporting strength | Deliberate weakness |
| --- | --- | --- | --- | --- | --- |
| Production | Industrialist | Rapid industrializer | Manufacturing scale | Construction | Does not solve infrastructure or state capacity |
| Production | Mercantile | Trade hub and coastal economy | Trade advantage | Ports and services | Weak without external trade |
| Production | Financial | Capital-rich state | Finance and investment | Tax collection and companies | Does not directly create resources or infrastructure |
| Production | Infrastructure | Large or dense country | Infrastructure capacity | Transport-sector throughput | Limited direct manufacturing power |
| Production | Extraction | Resource exporter | Agriculture and extraction | Discovery and depletion | Less useful to resource-poor states; oil capstone is late |
| Production | Labour | Labour-intensive economy | Workforce participation | Trade-union and worker institutions | Limited capital and construction support |
| Society | Academic | Research state | Innovation and research | Education | Does not solve fiscal or political capacity |
| Society | Bureaucratic | Centralized state | Bureaucratic capacity | Authority and administration | Limited market and military power |
| Society | Parliamentary | Reforming constitutional state | Law enactment | Legitimacy and IG management | No direct economic output |
| Society | Welfare | Mature social state | Population resilience | Migration and qualifications | Institution and welfare costs still require funding |
| Society | Diplomatic | Subject manager or expansionist | Diplomatic capacity | Relations and controlled infamy | No direct battlefield or production bonus |
| Society | Nationalist | Homogenizing nation-state | Assimilation and conversion | Loyalism and prestige | Reduced migration attraction |
| Society | Reformist | Pluralist reform state | Tolerance and migration | Turmoil management | Reduced authority |
| Military | Offensive | Aggressive land power | Army offense | Capture and recovery | Does not improve manpower or military industry |
| Military | Defensive | Attritional land power | Army defense | Supply and war exhaustion | Limited offensive tempo |
| Military | Naval | Maritime power | Fleet quality | Raiding and invasion | Low value to landlocked states |
| Military | Professional Army | Small high-quality military | Training and readiness | Mobility and prestige | Higher military wage burden |
| Military | Mass Conscription | Population-rich mass army | Conscription capacity | Military production | Higher casualty exhaustion and supply burden |
| Military | Colonial | Overseas empire | Colony growth | Unincorporated-state migration and output | Low value without overseas expansion |
| Military | War Economy | Late-game total-war state | Military industry | Strategic military goods | Arrives late and has little peacetime utility |

## First balance-pass targets

- Industrialist construction total: 10%.
- Labour working-adult-ratio total: +0.03.
- Parliamentary law-enactment speed total: 20%; success total: +0.10.
- Diplomatic infamy decay total: 25%; generation: -10%.
- Offensive army offense multiplier total: 15%, plus limited flat offense.
- Defensive army defense multiplier total: 15%.
- Welfare mortality total: -6%.
- Infrastructure infrastructure multiplier total: 25%.
- Bureaucratic bureaucracy multiplier total: 25%.

These are initial targets, not permanent guarantees. Runtime campaign tests should
measure pick rates and outcomes before a second numerical pass.

## Runtime test matrix

Test at least one major industrial power, one small developing state, one
land-focused military power, and one naval/colonial power. Record at 1850, 1875,
1900, and 1925:

- embraced and completed groups;
- AI choices and exclusive-pair violations;
- current idea points and next costs;
- national idea unlock count;
- construction, bureaucracy, infamy, law enactment, mortality, offense, and defense;
- whether the Extraction capstone and War Economy gates work;
- false alerts, missing tooltips, panel overflow, and script errors.
