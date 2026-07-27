# Grup Fikirleri (Idea Groups) Refactor & Denge Planı

> **2026-07-26 ikinci denge turu güncellemesi:** Bu dosya ilk refactor'ın tarihsel
> handoff kaydıdır. Güncel grup rolleri, güç bantları ve test hedefleri için
> [`IDEA_GROUP_BALANCE.md`](IDEA_GROUP_BALANCE.md) esas alınır. Grup modifier'ları
> artık generated kabul edilmez; elle bakımı yapılır. `national_idea_pool` ham
> fikir sayısından değil tamamlanan grup sayısından yeniden hesaplanır.

> **Bu doküman bir handoff belgesidir.** Oturum/hesap değişse bile buradan devam edilebilir.
> Yazıldığı tarih: 2026-07-26 · Branch: `master`
> Talep eden karar: EU4 taklidi olan grup fikirlerini Victoria 3'ün kendi konseptine oturtmak + dengeyi düzeltmek.

---

## 0. Bu planı okuyan yeni oturum için: durum özeti

**İlerleme:** Faz 0–3, Faz 4a–4e ve Faz 5 tamamlandı (§6). **Planlanan tüm script işi bitti.**
Mod oyunda açıldı, panel yüklendi, **log'da bu refactor'a ait hata yok** (§6b).
Kalan: **4f (ikonlar) — kullanıcıya bağlı**, özgün .dds sanat üretilemiyor. Ve **hiçbir faz oyunda test edilmedi.**
**20 grubun tamamı artık veri, script ve GUI katmanlarında bağlı ve tutarlı.**
20 grubun içerik tasarımı kilitlendi ve `ve_group_ideas.txt` tek kaynaktan üretiliyor; script'ler scratchpad'de (`ideas_design.py` = tasarım tablosu, `gen_group_ideas.py` = üreteç). **Bu iki dosya sonraki alt adımların da kaynağıdır — kalıcı saklanmaları gerekirse repoya taşınmalı.**
Faz 0–1 davranış-nötr; Faz 2 dengeyi, Faz 3 isimleri bilinçli değiştirdi. **Dördü de oyun içi test bekliyor.**
**⚠️ Faz 3 mevcut kayıtları bozdu** (identifier rename kararı gereği) — test için yeni oyun başlatılmalı.

### Dersler (sonraki fazlarda uygulanmalı)

1. **Modifier içeriğini yeniden dizerken dış bağımlılıkları tara.** Faz 2'de `ethnocentrism_idea_2_mdf`'i conversion/assimilation olarak ikiye böldüm; [`missionary_value.txt`](common/script_values/missionary_value.txt) o modifier'ı 14 yerde kontrol ediyordu (7 dini + 7 kültürel misyoner gücü) ve bağ koptu. Faz 3'te yakalanıp onarıldı. **Kural:** bir modifier'ın içeriğini değiştirmeden önce `grep -r "has_modifier = <ad>"` çalıştır. Bilinen dış bağımlılıklar: `nationalist_idea_2_mdf` (14×, misyoner gücü — **bölünemez**), `naval_idea_4_mdf` (ve_ages + ve_ai_effects), `economic_idea_7_mdf` (Economic_Idea.txt flavor event'i).
2. **Rename'de alt-string tuzağına dikkat.** Grup adları hem başka modifier adlarının (`state_trade_advantage_mult`) hem texture dosya adlarının (`idea_humanist_ideas.dds`) içinde geçiyor. Her zaman `<grup>_idea(?!s)` gibi sınır-duyarlı regex kullan ve texture yollarının değişmediğini assert et.
3. **Satır sonu kontrolü için `tr -dc '\r' | wc -c` kullan.** `cat -A` Git Bash pipeline'ında CR'ı yutuyor ve `core.autocrlf = true` olduğu için `git diff` de maskeliyor — bu oturumda iki kez yanlış alarma yol açtı.
4. **Sıralama dersi:** İçerik dengesini (Faz 2) yeniden adlandırma/yapılandırmadan (Faz 3–4) **önce** yapmak hataydı; Faz 4'te 4 grubun içeriği yeniden dağıtılacağı için o kısım iki kez elden geçiyor. Benzer işlerde önce yapı, sonra denge.

**Faz 2 sonrası önemli not:** Oyuncunun gördüğü fikir tooltip'leri [`ve_idea_tooltip_effects.txt`](common/scripted_effects/ve_idea_tooltip_effects.txt)'teki `idea_N_tt_effects` tarafından `add_modifier` ile **otomatik türetiliyor** — yani `ve_group_ideas.txt`'i değiştirmek tooltip'i kendiliğinden günceller, elle senkron gerekmez. Tek istisna `custom_tooltip` kullanan ethnocentrism 5 ve 7.

Aynı oturumda plan dışında yapılmış 2 küçük düzeltme (bağımsız, tamamlanmış):

1. [`common/history/states/ve_states.txt:92`](common/history/states/ve_states.txt) — `syndicalism_idea`'yı taşıyan state `STATE_ANDALUSIA` → `STATE_EAST_ANGOLA` olarak değiştirildi. Başka referansı yoktu.
2. [`common/scripted_effects/ve_set.txt`](common/scripted_effects/ve_set.txt) — `set_missionary_cultural_missionary` içindeki 3 satırda `set_variable` adları yanlışlıkla `ve_` prefix'liydi (`ve_total_culture_missionaries`, `ve_avaible_missionaries`, `ve_total_missionaries`) ama `has_variable` kontrolleri prefix'sizi arıyordu. Prefix'ler kaldırıldı. Bu, `ve_religion.txt:2182`'de tekrarlayan `Value of wrong type ... type 'none'` hata loglarının kaynağıydı. **Oyunda doğrulanması bekliyor.**

---

## 1. Mevcut sistemin röntgeni (doğrulanmış)

### Ekonomi
| Değer | Yer |
|---|---|
| Aylık gelir: **13** (oyuncu) + okuryazarlıktan **1–4** ≈ **15/ay** | [`ve_script_values.txt:979`](common/script_values/ve_script_values.txt) `monthly_idea_points` |
| Fikir maliyeti: **300 sabit** | [`ve_scripted_effects.txt:181`](common/scripted_effects/ve_scripted_effects.txt) `idea_cost` |
| Satın alma eşiği: `idea_point_value >= 300` | [`ve_scripted_triggers.txt:254`](common/scripted_triggers/ve_scripted_triggers.txt) `idea_cost_trigger` |
| Slot: 10 yılda 1, **maks 8** | `embrace_idea_tt` loc, `idea_group_unlocked` değişkeni |
| Her fikir `national_idea_pool` +1 (tavan 200) | [`ve_idea_effects.txt`](common/scripted_effects/ve_idea_effects.txt) |
| Her 3 `national_idea_pool` = 1 ulusal fikir kademesi | [`ve_national_ideas.txt`](common/scripted_guis/ve_national_ideas.txt) (`>= 3`, `>= 6`, `>= 9` …) |

**Sonuç:** 100 yıl ≈ 18.000 puan ≈ 60 fikir. Tavan 8×7 = **56**. Bütçe tavandan **fazla** → oyuncu seçtiği her şeyi bitirir, seçim gerilimi yok, sadece sıralama gerilimi var. Erken oyunda slot yok ama puan akar (taşma), geç oyunda harcanacak yer kalmaz.

### Mevcut 15 grup
- **ADM:** Innovative, Economic, Administrative, Ethnocentrism, Politics
- **DIP:** Diplomatic, Trade, Qualification, Humanist, Syndicalism
- **MIL:** Offensive, Defensive, Naval, Militarization, Imperialist

### Age sistemi — ÖNEMLİ DÜZELTME
İlk teşhiste "Age ilerlemesi yok, sadece debug event'lerinde" denmişti. **Bu yanlıştı.** Dosya adı `developer_events.txt` olduğu için debug sanıldı; oysa `dev.5` ve `dev.6` gerçek oyun event'leri ve [`ve_code_on_actions.txt:15`](common/on_actions/ve_code_on_actions.txt)'te `on_yearly_pulse_country`'ye kayıtlı.

| Age | Loc adı | Global | Event | Tarih |
|---|---|---|---|---|
| 1 | "Age of Victoria" | `ve_age_1_started` | [`ve_global.txt:3`](common/history/global/ve_global.txt) | başlangıç → 1870 |
| 2 | "Imperialism Age" | `ve_age_2_started` | [`dev.5`](events/developer_events.txt) | `year >= 1871`, `< 1906` |
| 3 | "The Great Wars Age" | `ve_age_3_started` | [`dev.6`](events/developer_events.txt) | `year >= 1906` |

Age ilerlemesi **çalışıyor ve zaten tarih tabanlı.** Karar: mevcut tarihler (1836/1871/1906) korunacak.

Her age'in 11 bonusu (`ve_age_bonus_1..11`) ve 7 objective'i (`ve_age_obj_1..7`) var; age geçişinde önceki age'in bonus modifier'ları kaldırılıp `ve_splender_points` sıfırlanıyor.

**Age sisteminde bulunan 2 küçük kusur (Faz 0'a alındı):**
1. Her iki geçiş event'inin trigger'ı `is_ai = yes`. `dev.5`'te `hidden = yes` var ama **`dev.6`'da yok** → gösterilmek istenen event bir AI ülkesine gidiyor, oyuncu age değişiminden hiç haberdar olmuyor.
2. [`ve_global.txt:3`](common/history/global/ve_global.txt) yorumu `#Victorian Age - 1936` diyor; Age 1 aslında 1870'te bitiyor.

---

## 2. Teşhis: yapısal problemler

**P1 — ADM/DIP/MIL üçlüsü tamamen dekoratif.**
EU4'te bu kolonlar ayrı para birimleriydi. Burada tek havuz var (`idea_point_pool`, 300/fikir), yani kolonlar hiçbir şeyi kısıtlamıyor.

**P2 — Grup tamamlama ödülü (ambition) yok.**
[`ve_idea_effects.txt:215`](common/scripted_effects/ve_idea_effects.txt) → 7. fikirden sonra sadece `set_variable = <grup>_completed`, o da yalnızca butonu gizliyor. Grubu bitirmenin payoff'u sıfır.

**P3 — 7. fikir capstone değil.**
`trade_idea_1` = `state_trade_advantage_mult 0.15`, `trade_idea_7` = **aynı modifier, 0.10**. Capstone giriş fikrinden zayıf. Fikir başına güç bütçesi disiplini yok (`offensive_idea_5` tek zayıf efekt vs `defensive_idea_1` iki güçlü efekt).

**P4 — Flat `_add` değerleri 100 yıl boyunca ölçeklenmiyor.**
`innovative_idea_4` = **+300 bureaucracy**. Vanilla'da flat bureaucracy buff'ı pratikte yok (base 100, en büyük malus −25). 1836'da oyun bozucu, 1936'da görünmez. Aynı sorun: `country_authority_add 250/100`, `country_prestige_add 50`, `country_tech_spread_add 15`, `country_diplomatic_play_maneuvers_add 25`, `country_authority_per_subject_add 100`.
Ayrıca Innovative, Administrative'den (250) **daha fazla** bürokrasi veriyor → kimlik çakışması.

**P5 — Kimlik dağılması / duplikasyonlar.**

| Modifier | Nerede |
|---|---|
| `state_education_access_wealth_add 0.002` | innovative_5, qualification_2, humanist_4 (**3 grup, birebir aynı**) |
| `country_production_tech_research_speed_mult` | innovative_7 (%5), economic_6 (%5), **diplomatic_6 (%7.5)** |
| `country_improve_relations_speed_mult 0.15` | diplomatic_4, humanist_6 |
| `state_migration_pull_mult` | qualification_1 (%25), humanist_7 (%20) |
| `country_influence_mult 0.1` | diplomatic_1, imperialist_5 |
| `country_minting_mult 0.1` | economic_3, trade_2 |
| `state_trade_advantage_mult` | trade_1 (%15), trade_7 (%10) — **aynı grup içinde** |

Diplomasi grubunun oyundaki en iyi üretim araştırma bonusunu vermesi başlı başına hatalı.

**P6 — Tematik tutarsızlıklar.**
- `qualification_idea_7`: 9 rastgele `goods_output` +%10 (likör, şarap, kumaş, meyve, şeker, **radyo**, ipek, **elektrik**, **petrol**) — eğitim grubunda sanayi paketi.
- `qualification_idea_5`: `state_pop_qualifications_mult = 0.35` — vanilla'daki en büyük tek kaynak 0.25 (bir decree), tipik 0.05–0.20. **Oyundaki en güçlü kaynak.**
- **Syndicalism** içeriği demografi (working adult ratio, mortality, birth rate) → bu "Refah", sendikalizm değil.
- **Imperialist** MIL kolonunda ama içeriği sömürgeleştirme/prestij/kaynak = ekonomi/diplomasi işi.
- `ethnocentrism_idea_5` ve `_7` **boş modifier blokları** (sadece `#Missionary Power` yorumu); efekt başka yerde ama tooltip'te boş modifier görünüyor.
- Boolean unlock'lar stat fikirlerine karışmış: `trade_idea_2` (`country_can_form_construction_company_bool`), `ethnocentrism_idea_1` (`country_higher_diplomatic_acceptance_same_religion_bool`).

**P7 — Anakronizm.** 15 grup da 1836'da açık. Syndicalism, radyo/elektrik/petrol bonusları başlangıçta alınabiliyor. Ages sistemi ile ideas sistemi tamamen kopuk.

**P8 — Boilerplate.** [`ve_idea_effects.txt`](common/scripted_effects/ve_idea_effects.txt) 3250 satır, 15 tane neredeyse birebir aynı ~215 satırlık blok.

### Hata olmayan, dokunulmayacak
`innovative_idea_6` → `state_urbanization_per_level_mult = -0.15`. Vanilla society teknolojileri de −0.1/−0.15/−0.25 kullanıyor; **negatif burada bonus.** Değeri korunarak P4 Altyapı grubuna taşınacak.

---

## 3. Alınan kararlar

| # | Karar |
|---|---|
| 1 | Kolonlar → **Production / Society / Military** (Vic3'ün 3 teknoloji ağacı) |
| 2 | **20 grup girişi / 18 seçilebilir yol** (2 dışlayan çift) |
| 3 | **Kademeli fikir maliyeti** eklenecek |
| 4 | **Age kapısı** eklenecek (tarih tabanlı, mevcut 1836/1871/1906 korunur) |
| 5 | **Boilerplate refactoru** yapılacak |
| 6 | **Ambition (grup tamamlama ödülü)** eklenecek |
| 7 | Dışlayan çiftler **tek satırda** gösterilecek, yol seçimi benimseme anında yapılacak (GUI işi daha fazla, kabul edildi) |
| 8 | İkonlar: mevcut vanilla/mod ikonlarından tematik seçim + mod-local kopya. **Özgün `.dds` çizilemez** — bu sınır kabul edildi |

---

## 4. Hedef tasarım

### 4.1 Kolonlar

`adm_ideas` / `dip_ideas` / `mil_ideas` → **`prod_ideas` / `soc_ideas` / `mil_ideas`**

| Eski loc key | Yeni | Metin |
|---|---|---|
| `ADM_HEADER` "Administrative Ideas" | `PROD_HEADER` | "Production Ideas" |
| `DIP_HEADER` "Diplomatic Ideas" | `SOC_HEADER` | "Society Ideas" |
| `MIL_HEADER` "Military Ideas" | `MIL_HEADER` | "Military Ideas" |

Not: Vic3'ün Society teknoloji ağacı diplomasi teknolojilerini (Nationalism, Pan-Nationalism, International Relations) içeriyor → **Diplomatic grubu Society kolonuna doğal oturur**, zorlama değil.

### 4.2 Grup haritası

Dışlayan çiftler listede **2 satır** kaplar, **1'i** benimsenebilir → 6/6/6 = **18 seçilebilir yol**.
🔒 = Age kapısı. ⟷ = dışlayan çift.

#### ÜRETİM — 6 satır / 6 seçilebilir

| ID | Grup | Kimlik | Kaynak |
|---|---|---|---|
| P1 | **Sanayici** (Industrialist) | İnşaat + ağır/hafif sanayi | eski Economic (inşaat kısmı) |
| P2 | **Tüccar** (Mercantile) | Ticaret avantajı, kapasite, liman | eski Trade |
| P3 | **Maliye** (Financial) | Vergi, kredi, sermaye, şirket | **YENİ** — eski Economic'in para kısmından ayrılır |
| P4 | **Altyapı** (Infrastructure) | Demiryolu, altyapı, kentleşme | **YENİ** + eski `innovative_idea_6` |
| P5 | **Toprak & Maden** (Extraction) | Tarım, madencilik, petrol, kaynak | eski Imperialist (kaynak kısmı) + `economic_idea_7` |
| P6 | **Emek** (Labour) 🔒Age 2 | Sendika, ücret, işgücü oranı | eski Syndicalism (gerçek kimliğine oturtulur) |

#### TOPLUM — 7 satır / 6 seçilebilir

| ID | Grup | Kimlik | Kaynak |
|---|---|---|---|
| S1 | **Akademi** (Academic) | İnovasyon, üniversite, okuryazarlık, qualification | eski Innovative + Qualification (eğitim kısmı) |
| S2 | **Bürokrasi** (Bureaucratic) | Devlet kapasitesi, kararname, otorite | eski Administrative |
| S3 | **Parlamento** (Parliamentary) | Meşruiyet, yasa çıkarma, IG | eski Politics |
| S4 | **Refah** (Welfare) 🔒Age 2 | Ölüm oranı, doğum, göç, yaşam standardı | eski Syndicalism (demografi) + `qualification_idea_6` |
| S5 | **Diplomasi** (Diplomatic) | Etki, itibar, infamy, tabiler | eski Diplomatic |
| S6a | **Milliyetçi** (Nationalist) 🔒Age 2 ⟷ | Asimilasyon, dönüşüm, misyoner | eski Ethnocentrism |
| S6b | **Reformcu** (Reformist) 🔒Age 2 ⟷ | Hoşgörü, radikal azaltma, göç çekimi | eski Humanist |

#### ORDU — 7 satır / 6 seçilebilir

| ID | Grup | Kimlik | Kaynak |
|---|---|---|---|
| M1 | **Taarruz** (Offensive) | Saldırı, arazi, ilerleme | aynı |
| M2 | **Savunma** (Defensive) | Savunma, moral, kayıp | aynı |
| M3 | **Bahriye** (Naval) | Zırh, isabet, çıkarma, konvoy | aynı |
| M4 | **Sömürge** (Colonial) 🔒Age 2 | Sömürge büyümesi, deniz aşırı ölüm oranı | eski Imperialist (sömürge kısmı) |
| M5 | **Harp Sanayii** (War Economy) 🔒Age 3 | Askeri sanayi, silah/mühimmat üretimi | **YENİ** |
| M6a | **Profesyonel Ordu** (Professional Army) ⟷ | Eğitim, kalite, lojistik | eski Militarization |
| M6b | **Halk Ordusu** (Mass Conscription) ⟷ | Celp oranı, ucuz kitle ordusu | **YENİ** |

**Silinen grup yok.** 15 eski grubun hepsi korunur veya bölünür; 5 yeni yol gelir (Financial, Infrastructure, War Economy, Mass Conscription + Welfare/Labour ayrımı).

### 4.3 Güç bütçesi kuralları

Şu anki en büyük denge kırığı fikir başına bütçe disiplini olmaması. Uygulanacak kurallar:

1. **1 fikir = 1 birim.** Tek modifier: throughput `+0.10`, research `+0.05`, generic mult `+0.10~0.15`, havuz mult `+0.10`.
2. **İki modifier varsa her biri yarım** (`+0.05 / +0.05`). Zayıf/niş modifier'lar (arazi bonusları, küçük goods) istisna — ikisi birlikte 1 birim sayılır.
3. **7. fikir (capstone) = 1.5–2 birim** ve grubun kimlik modifier'ını taşır. Bu kural `trade_7 < trade_1` tersliğini yapısal olarak imkânsız kılar.
4. **Ambition = 2 birim**, ayrı kalıcı modifier (`<grup>_ambition_mdf`), 7. fikir alındığında eklenir.
5. **Flat `_add` yasağı** havuz kaynaklarında. Motorda `_mult` karşılıkları **doğrulandı**: `country_bureaucracy_mult`, `country_authority_mult`, `country_prestige_mult`, `country_tech_spread_mult`, `country_influence_mult`.
   Flat kalabilecekler: `country_legitimacy_base_add` (0–100 ölçekli), `state_education_access_add`, `state_birth_rate_mult` gibi zaten oran olanlar.
6. **Modifier tekliği:** bir modifier tipi tek bir grubun kimliğine aittir. §2/P5'teki 7 duplikasyonu bu kural çözer.
7. **Aykırı değer tavanı:** `state_pop_qualifications_mult` 0.35 → **0.15**.
8. **Boolean'lar capstone veya ambition'a taşınır** (all-or-nothing ödül olarak doğru yer).

### 4.4 Kademeli maliyet

| | Şimdi | Hedef |
|---|---|---|
| Fikir maliyetleri | 300 ×7 | **200 / 250 / 300 / 375 / 450 / 550 / 675** |
| Grup toplamı | 2.100 | **2.800** |
| İlk fikre süre | 20 ay | **13 ay** |
| 8 grubu bitirme | 16.800 | **22.400** |
| 100 yıllık bütçe | ~18.000 | ~18.000 |
| Sonuç | tavandan 1.200 fazla → hepsi alınır | **4.400 açık → ~6.4 grup bitirilebilir** |

Slot sayısı (8) ve 10 yıllık açılış korunur. `idea_cost` artık sabit 300 çıkarmak yerine grup içi seviyeye göre kademeli çıkarmalı → `idea_cost_trigger` de aynı kademeyi kontrol etmeli.

⚠️ **Yan etki — kalibre edilmeli:** toplam fikir sayısı ~60 → ~45'e düşer, dolayısıyla `national_idea_pool` yavaşlar ve ulusal fikir kademeleri gecikir. [`ve_national_ideas.txt`](common/scripted_guis/ve_national_ideas.txt)'teki kademe sayısı sayılıp fikir başına +1 yerine kademeli artış verilmeli veya eşikler (3/6/9…) düşürülmeli.

### 4.5 Age kapısı — kritik uygulama detayı

`ve_age_2_started` global'i **Age 3 başlarken siliniyor** ([`dev.6`](events/developer_events.txt), `remove_global_variable = ve_age_2_started`). Dolayısıyla:

```
# YANLIŞ — Age 2'de açılan grup Age 3'te tekrar kilitlenir
has_global_variable = ve_age_2_started
```

Doğrusu, kodda **zaten var olan ve hiç silinmeyen** kalıcı guard değişkenlerini kullanmak:

```
# DOĞRU — kalıcı
has_global_variable = age_2_started_trigger
has_global_variable = age_3_started_trigger
```

Bunlar `dev.5` ve `dev.6` içinde `set_global_variable` ile bir kez set ediliyor, hiçbir yerde `remove` edilmiyor. `age_1_started_trigger` yok — gerekmiyor, Age 1 grupları kapısız.

**Kapı yerleşimi:**
- **Age 1 (kapısız):** P1, P2, P3, P4, P5, S1, S2, S3, S5, M1, M2, M3
- **🔒Age 2:** P6 Emek, S4 Refah, S6a/S6b Milliyetçi⟷Reformcu, M4 Sömürge
- **🔒Age 3:** M5 Harp Sanayii
- **Fikir seviyesinde kapı:** P5 Extraction'ın capstone'u (petrol) 🔒Age 3

### 4.6 Dışlayan çift mekaniği

`embrace_idea_group`'un `is_shown`'ında karşı tarafın `can_go_*` değişkeni kontrol edilir:

```
flag:nationalist_idea = {
    NOT = { has_variable = can_go_nationalist }
    NOT = { has_variable = can_go_reformist }   # ← eklenen satır
}
```

**Karar 7 gereği** liste tek satır gösterecek: satır benimsenmeden önce iki yolu sunan bir seçim adımı (iki butonlu küçük blok) gelir, seçim yapıldıktan sonra satır seçilen yolun kimliğine döner ve diğer yol kalıcı kapanır. GUI'de kilitli tarafa gri ikon + açıklayıcı tooltip.

---

## 5. Fikir iskeleti (ilk taslak — Faz 2/4'te ince ayar)

> ⚠️ Aşağıdaki atamalar **ilk taslaktır.** Uygulama sırasında iki denetim zorunlu:
> **(a) varlık denetimi** — her modifier adının motorda var olduğu doğrulanmalı;
> **(b) duplikasyon denetimi** — §4.3/kural 6 gereği hiçbir modifier iki grupta olmamalı.
> `⚠️` işaretli olanların adı veya büyüklüğü henüz doğrulanmadı.

### P1 · Sanayici (Industrialist)
1. `state_construction_mult = 0.05`
2. `building_group_bg_light_industry_throughput_add = 0.10`
3. `goods_output_tools_mult = 0.10`
4. `building_group_bg_heavy_industry_throughput_add = 0.10`
5. `country_company_construction_efficiency_bonus_add = 0.10`
6. `building_group_bg_manufacturing_throughput_add = 0.10`
7. **Capstone:** `state_construction_mult = 0.10` + `building_group_bg_heavy_industry_throughput_add = 0.05`
- **Ambition:** `state_construction_mult = 0.10`

### P2 · Tüccar (Mercantile)
1. `state_trade_advantage_mult = 0.10`
2. `state_trade_capacity_mult = 0.10`
3. `building_port_throughput_add = 0.10`
4. `state_trade_advantage_from_capacity_add = 0.10`
5. `country_company_throughput_bonus_add = 0.15`
6. `building_group_bg_service_throughput_add = 0.10`
7. **Capstone:** `state_trade_advantage_mult = 0.15` + `state_trade_capacity_mult = 0.05`
- **Ambition:** `country_can_form_construction_company_bool = yes` ⚠️ + `state_trade_advantage_mult = 0.05`

### P3 · Maliye (Financial)
1. `state_tax_waste_add = -0.10`
2. `country_minting_mult = 0.10`
3. `country_loan_interest_rate_mult = -0.10`
4. `state_tax_collection_mult = 0.06`
5. `country_max_companies_add = 1`
6. `state_capitalists_investment_pool_efficiency_mult = 0.15`
7. **Capstone:** `country_consumption_tax_cost_mult = -0.15` + `state_tax_collection_mult = 0.06`
- **Ambition:** `country_minting_mult = 0.10`

### P4 · Altyapı (Infrastructure)
1. `state_infrastructure_mult = 0.10`
2. `building_group_bg_infrastructure_throughput_add = 0.10`
3. `state_infrastructure_from_population_mult = 0.10`
4. `state_urbanization_per_level_mult = -0.10`
5. `building_group_bg_logging_throughput_add = 0.10`
6. `goods_output_coal_mult = 0.10` ⚠️
7. **Capstone:** `state_infrastructure_mult = 0.15` + `building_group_bg_infrastructure_throughput_add = 0.05`
- **Ambition:** `state_urbanization_per_level_mult = -0.10`

### P5 · Toprak & Maden (Extraction)
1. `building_group_bg_agriculture_throughput_add = 0.10`
2. `building_group_bg_mining_throughput_add = 0.10`
3. `country_resource_discovery_chance_mult = 0.15`
4. `building_group_bg_ranching_throughput_add = 0.10` + `building_group_bg_plantations_throughput_add = 0.10`
5. `country_resource_depletion_chance_mult = -0.15`
6. `building_group_bg_fishing_throughput_add = 0.10` + `building_group_bg_whaling_throughput_add = 0.10`
7. **Capstone** 🔒Age 3: `building_group_bg_oil_extraction_throughput_add = 0.15` + `building_group_bg_extraction_throughput_add = 0.05`
- **Ambition:** `building_group_bg_agriculture_throughput_add = 0.10`

### P6 · Emek (Labour) 🔒Age 2
1. `state_working_adult_ratio_add = 0.03`
2. `interest_group_ig_trade_unions_approval_add = 1`
3. `state_dependent_wage_mult = 0.15`
4. `state_farmers_investment_pool_efficiency_mult = 0.15` + `state_shopkeepers_investment_pool_efficiency_mult = 0.15`
5. `state_pop_pol_str_mult = 0.10`
6. `interest_group_ig_trade_unions_pol_str_mult = 0.15`
7. **Capstone:** `state_working_adult_ratio_add = 0.03` + `state_dependent_wage_mult = 0.10`
- **Ambition:** `state_working_adult_ratio_add = 0.02`

### S1 · Akademi (Academic)
1. `country_weekly_innovation_mult = 0.10`
2. `state_education_access_add = 0.02`
3. `building_university_throughput_add = 0.15`
4. `state_literacy_growth_add = 0.02` ⚠️ (büyüklük)
5. `country_tech_spread_mult = 0.10`
6. `state_pop_qualifications_mult = 0.15`
7. **Capstone:** `country_production_tech_research_speed_mult = 0.05` + `country_military_tech_research_speed_mult = 0.05` + `country_society_tech_research_speed_mult = 0.05`
- **Ambition:** `building_art_academy_throughput_add = 0.20` + `country_weekly_innovation_mult = 0.05`

### S2 · Bürokrasi (Bureaucratic)
1. `country_bureaucracy_mult = 0.10`
2. `building_group_bg_government_throughput_add = 0.10`
3. `state_bureaucracy_population_base_cost_factor_mult = -0.10`
4. `country_authority_mult = 0.10`
5. `state_decree_cost_mult = -0.15`
6. `country_government_wages_mult = -0.15`
7. **Capstone:** `country_bureaucracy_mult = 0.15` + `state_decree_cost_mult = -0.10`
- **Ambition:** `country_authority_mult = 0.10`

### S3 · Parlamento (Parliamentary)
1. `country_legitimacy_base_add = 10`
2. `country_law_enactment_speed_mult = 0.15`
3. `country_law_enactment_success_add = 0.05`
4. `country_law_enactment_stall_mult = -0.10`
5. `country_law_enactment_max_setbacks_add = 1`
6. `interest_group_approval_add = 1`
7. **Capstone:** `country_legitimacy_headofstate_add = 10` + `country_law_enactment_speed_mult = 0.10`
- **Ambition:** `country_law_enactment_success_add = 0.05`

### S4 · Refah (Welfare) 🔒Age 2
1. `state_mortality_mult = -0.03`
2. `state_birth_rate_mult = 0.02`
3. `state_migration_pull_mult = 0.20`
4. `state_welfare_payments_mult = -0.15`
5. `state_political_strength_from_welfare_mult = 0.15`
6. `country_standard_of_living_full_acceptance_add = 2` + `..._second_rate_citizen_add = 2` + `..._open_prejudice_add = 1` + `..._cultural_erasure_add = 1` + `..._violent_hostility_add = 1` *(eski `qualification_idea_6`, tek paket olarak 1 birim)*
7. **Capstone:** `state_mortality_mult = -0.03` + `state_birth_rate_mult = 0.015`
- **Ambition:** `state_migration_pull_mult = 0.15`

### S5 · Diplomasi (Diplomatic)
1. `country_influence_mult = 0.10`
2. `country_improve_relations_speed_mult = 0.15`
3. `country_infamy_decay_mult = 0.25`
4. `country_authority_per_subject_add = 50` + `country_subject_income_transfer_mult = 0.10`
5. `country_prestige_mult = 0.075`
6. `country_damage_relations_speed_mult = 0.15`
7. **Capstone:** `country_diplomatic_play_maneuvers_add = 15` + `country_influence_mult = 0.10`
- **Ambition:** `country_infamy_decay_mult = 0.15`

### S6a · Milliyetçi (Nationalist) 🔒Age 2 ⟷
1. `state_assimilation_mult = 0.25`
2. `state_conversion_mult = 0.25`
3. `country_loyalism_increases_full_acceptance_mult = 0.25` + `country_loyalism_increases_second_rate_citizen_mult = 0.25`
4. Misyoner gücü +%0.7 *(mod mekaniği — eski `ethnocentrism_idea_5`, boş modifier bloğu düzeltilecek)*
5. `country_loyalists_from_legitimacy_mult = 0.20`
6. `state_loyalism_increases_cultural_erasure_mult = 0.25` + `state_loyalism_increases_open_prejudice_mult = 0.25`
7. **Capstone:** +2 misyoner *(eski `ethnocentrism_idea_7`)* + `state_assimilation_mult = 0.15`
- **Ambition:** `country_higher_diplomatic_acceptance_same_religion_bool = yes` + `state_conversion_mult = 0.15`

### S6b · Reformcu (Reformist) 🔒Age 2 ⟷
1. `state_radicalism_increases_violent_hostility_mult = -0.03` + `..._cultural_erasure_mult = -0.03` + `..._open_prejudice_mult = -0.03`
2. `state_loyalism_increases_violent_hostility_mult = 0.10`
3. `country_agitator_slots_add = 1`
4. `state_turmoil_effects_mult = -0.05`
5. `state_radicals_from_political_movements_mult = -0.15`
6. `state_loyalists_from_political_movements_mult = 0.15`
7. **Capstone:** `country_mass_migration_attraction_mult = 0.25` + `state_turmoil_effects_mult = -0.05`
- **Ambition:** `country_radicals_from_legitimacy_mult = -0.20`

### M1 · Taarruz (Offensive)
1. `unit_army_offense_add = 10`
2. `battle_offense_owned_province_mult = 0.10`
3. `unit_offense_developed_add = 5` + `unit_offense_forested_add = 5`
4. `unit_provinces_captured_mult = 0.15`
5. `unit_recovery_rate_add = 0.10`
6. `unit_offense_hazardous_add = 10`
7. **Capstone:** `unit_army_offense_mult = 0.15`
- **Ambition:** `unit_army_offense_add = 5` + `unit_provinces_captured_mult = 0.10`

### M2 · Savunma (Defensive)
1. `battle_defense_owned_province_mult = 0.10`
2. `unit_morale_damage_mult = 0.10` + `unit_morale_recovery_mult = 0.10`
3. `unit_provinces_lost_mult = -0.15`
4. `unit_defense_forested_add = 10` + `unit_defense_hazardous_add = 10`
5. `unit_kill_rate_add = 0.08`
6. `country_war_exhaustion_casualties_mult = -0.15`
7. **Capstone:** `unit_army_defense_mult = 0.15`
- **Ambition:** `unit_army_defense_add = 5` + `unit_provinces_lost_mult = -0.10`

### M3 · Bahriye (Naval)
1. `ship_supply_capacity_mult = 0.10`
2. `ship_armor_mult = 0.10`
3. `building_naval_administration_throughput_add = 0.15`
4. `ship_naval_invasion_efficiency_mult = 0.25`
5. `character_convoy_raiding_mult = 0.25`
6. `country_prestige_from_navy_power_projection_mult = 0.10`
7. **Capstone:** `ship_accuracy_mult = 0.15` + `ship_max_distance_to_port_add = 20`
- **Ambition:** `ship_armor_mult = 0.10` + `ship_accuracy_mult = 0.05`

### M4 · Sömürge (Colonial) 🔒Age 2
1. `state_colony_growth_speed_mult = 0.15`
2. `state_non_homeland_colony_growth_speed_mult = 0.15`
3. `state_colony_growth_creation_factor = 0.10`
4. `state_non_homeland_mortality_mult = -0.15`
5. `country_radicals_from_conquest_mult = -0.25`
6. `state_migration_pull_unincorporated_mult = 0.20`
7. **Capstone:** `building_group_bg_rubber_throughput_add = 0.15` + `state_colony_growth_speed_mult = 0.10`
- **Ambition:** `state_non_homeland_colony_growth_speed_mult = 0.15`

### M5 · Harp Sanayii (War Economy) 🔒Age 3
1. `building_group_bg_military_industry_throughput_add = 0.10`
2. `country_military_goods_cost_mult = -0.10`
3. `goods_output_small_arms_mult = 0.10` ⚠️
4. `goods_output_artillery_mult = 0.10` ⚠️
5. `goods_output_ammunition_mult = 0.10` ⚠️
6. `building_group_bg_military_throughput_add = 0.10`
7. **Capstone:** `goods_output_explosives_mult = 0.10` ⚠️ + `building_group_bg_military_industry_throughput_add = 0.10`
- **Ambition:** `country_military_goods_cost_mult = -0.10`

### M6a · Profesyonel Ordu (Professional Army) ⟷
1. `building_training_rate_mult = 0.20`
2. `country_prestige_from_army_power_projection_mult = 0.05`
3. `unit_supply_consumption_mult = -0.15`
4. `military_formation_army_movement_speed_mult = 0.15` + `military_formation_fleet_movement_speed_mult = 0.15`
5. `country_military_tech_spread_mult = 0.10` ⚠️ *(adı doğrulanmalı; yoksa alternatif gerekir)*
6. `military_formation_mobilization_speed_mult = 0.20`
7. **Capstone:** `building_training_rate_mult = 0.20` + `unit_supply_consumption_mult = -0.10`
- **Ambition:** `military_formation_mobilization_speed_mult = 0.15`

### M6b · Halk Ordusu (Mass Conscription) ⟷
1. `state_conscription_rate_mult = 0.15`
2. `state_building_conscription_center_max_level_add = 2`
3. `country_military_wages_mult = -0.15`
4. `country_infamy_generation_mult = -0.15`
5. `state_conscription_rate_add = 0.02` ⚠️ (büyüklük)
6. `country_suppression_attraction_factor = -0.25`
7. **Capstone:** `state_conscription_rate_mult = 0.15` + `state_building_conscription_center_max_level_add = 1`
- **Ambition:** `state_conscription_rate_mult = 0.10`

---

## 6. Uygulama fazları

Her faz kendi başına oyunda test edilebilir. **Faz 4'e kadar oyuncuya görünen hiçbir şey bozulmaz.**

### Faz 0 — Age sistemi küçük düzeltmeleri ✅ **TAMAMLANDI** *(oyun içi test bekliyor)*
- [x] [`events/developer_events.txt`](events/developer_events.txt) `dev.6`'ya `hidden = yes` eklendi (satır 608)
- [x] Oyuncuya görünür age bildirim event'leri eklendi → yeni dosya [`events/ve_age_events.txt`](events/ve_age_events.txt), `namespace = ve_ages`, `ve_ages.1` (Age 2) ve `ve_ages.2` (Age 3)
- [x] `dev.5` ve `dev.6`'nın `immediate` bloklarına `every_country = { limit = { is_ai = no } trigger_event = ... }` eklendi → pulse gecikmesi yok, çok oyunculuda tüm insan oyuncular alır
- [x] Loc: `ve_age_notify_option` eklendi. Başlık/açıklama için mevcut `ve_imperialism_age_title/desc` ve `ve_great_wars_age_title/desc` yeniden kullanıldı — yeni metin gerekmedi
- [x] [`ve_global.txt:3`](common/history/global/ve_global.txt) yanıltıcı `#Victorian Age - 1936` yorumu düzeltildi

**Doğrulama yapıldı:** brace dengesi (developer_events 272/272, ve_age_events 6/6), `ve_ages.1/.2` referansları tanımlarla eşleşiyor, namespace çakışması yok, 5 loc anahtarının hepsi mevcut, satır sonları korundu (tüm dokunulan dosyalar saf CRLF).
**Kalan:** oyunda 1871 ve 1906'ya kadar ilerleyip bildirim event'lerinin göründüğünü ve age geçişinin bozulmadığını doğrulamak.

### Faz 1 — Boilerplate refactoru ✅ **TAMAMLANDI** *(oyun içi test bekliyor)*
- [x] Yeni paylaşılan effect: `ve_idea_purchase_common` → [`ve_scripted_effects.txt:189`](common/scripted_effects/ve_scripted_effects.txt). İçeriği `national_idea_pool` artırma + `idea_cost = yes`. `idea_cost` başka çağıranlar için olduğu gibi duruyor.
- [x] [`ve_idea_effects.txt`](common/scripted_effects/ve_idea_effects.txt): 105 branch'in hepsinde 9 satırlık `national_idea_pool` bloğu kaldırıldı ve `idea_cost = yes` → `ve_idea_purchase_common = yes` yapıldı. **3248 → 2299 satır (−949).**
- [x] **Bonus bug fix:** `boost_inno_idea_effect`'in ilk branch'inde `innovative_idea_1_mdf` iki kez ekleniyordu (biri korumasız, biri `if NOT has_modifier` korumalı). Korumasız olan kaldırıldı. 15 grup tarandı, bu tek anomaliydi.
- [x] ~~`ve_ai_effects.txt` / `ve_idea.txt` sadeleştirmesi~~ → **uygulanamaz.** İncelendi: `ve_ai_effects.txt`'teki 15 tekrar zaten tek satırlık `idea_cost_trigger = yes` çağrısı; [`ve_idea.txt`](common/scripted_guis/ve_idea.txt)'in `is_shown`/`is_valid` switch'lerindeki tekrar ise grup adına bağlı (`can_go_<grup>`, `<grup>_idea_completed`) ve motor dinamik değişken adı desteklemediği için faktörlenemiyor.

**Sıra değişikliği notu:** `national_idea_pool` artırma artık `add_modifier`'dan **sonra** çalışıyor (önce önceydi). İkisi farklı değişkenlere dokunduğu için etkileşim yok — davranış birebir aynı.

**Doğrulama yapıldı:** 15 effect bloğu, 105 branch, 105 çağrı, 1 tanım, 15 `_completed`, brace dengesi (758/758 ve 276/276), ethnocentrism özel branch'leri sağlam, satır sonları korundu, `git diff --numstat` = 105 ekleme / 1054 silme (945 pool + 105 idea_cost + 4 fazla add_modifier ✓).
**Kalan:** oyunda fikir satın alıp modifier'ın eklendiğini, puanın düştüğünü ve ulusal fikir kademelerinin açıldığını doğrulamak.

**Faz 1'de ortaya çıkan yeni bulgu → Faz 2'ye eklendi:** `ethnocentrism_idea_5_mdf` ve `ethnocentrism_idea_7_mdf` [`ve_group_ideas.txt`](common/static_modifiers/ve_group_ideas.txt)'te tanımlı ama **hiçbir effect tarafından eklenmiyor** (105 tanımlı modifier, 103'ü ekleniyor). O iki branch bunun yerine `ethnocentrism_idea_5_var` / `_7_var` ile özel misyoner mantığı çalıştırıyor. **Kritik:** idea 7'nin asıl ödülü olan +2 misyoner bloğu **tamamen yorum satırı** — yani 300 puanlık bu fikir `ve_law_change_effects` dışında hiçbir şey vermiyor. Yorumlanmış kod tam olarak bu oturumda [`ve_set.txt`](common/scripted_effects/ve_set.txt)'te düzeltilen `avaible_missionaries` / `total_missionaries` değişkenlerine referans veriyor — muhtemelen o prefix hatası yüzünden çalışmadığı için devre dışı bırakılmış. Prefix düzeltildiğine göre yeniden etkinleştirilebilir.

### Faz 2 — Denge düzeltmeleri ✅ **TAMAMLANDI** *(oyun içi test bekliyor — davranış bilinçli olarak değişti)*
- [x] [`ve_group_ideas.txt`](common/static_modifiers/ve_group_ideas.txt) baştan yazıldı. Grup adları ve 7-fikir yapısı **korundu** (yeniden adlandırma Faz 3'te).
- [x] **Duplikasyon: 0.** Denetim script'i ile doğrulandı — hiçbir modifier tipi birden fazla grupta geçmiyor. Temizlenenler: `state_education_access_wealth_add` (3 gruptaydı), 3 farklı gruptaki research_speed, `building_university_throughput_add`, `country_improve_relations_speed_mult`, `state_migration_pull_mult`, `country_influence_mult`, `country_minting_mult`, `state_construction_mult`, `state_birth_rate_mult`, `state_turmoil_effects_mult`, `country_agitator_slots_add`, `country_radicalism_increases_*`, `unit_offense_hazardous_add` (grup içi), `state_trade_advantage_mult` (grup içi).
- [x] **Flat → mult:** `country_bureaucracy_add 250/300` → `country_bureaucracy_mult 0.10`; `country_authority_add 250/100` → `country_authority_mult 0.10`; `country_prestige_add 50` → `country_prestige_mult 0.10`; `country_authority_per_subject_add 100` → `20` (vanilla tavanı).
- [x] **Aykırı değerler:** `state_pop_qualifications_mult` 0.35 → 0.15 (vanilla maks 0.20).
- [x] **Kaldırıldı:** `qualification_idea_7`'nin 9 rastgele `goods_output` paketi; `diplomatic_idea_6`'nın research_speed'i.
- [x] **Yükseltilen düşük değerler** (vanilla ölçeğine göre zayıftılar): `state_education_access_wealth_add` 0.002→0.005, `state_education_access_add` 0.02→0.05, `state_turmoil_effects_mult` −0.05→−0.10, `interest_group_approval_add` 1→2, `state_migration_pull_mult` 0.25→0.30, `country_loan_interest_rate_mult` −0.05→−0.10.
- [x] **Capstone:** 15 grubun hepsinde 7. fikir artık en güçlü ve grubun kimlik modifier'ını taşıyor. `trade_idea_7` tersliği giderildi (0.10 → 0.15, idea 1 0.15 → 0.10). Booleanlar capstone'a taşındı.
- [x] **Ölü modifier tanımları silindi:** `ethnocentrism_idea_5_mdf` / `_7_mdf`. Hiçbir effect eklemiyordu ve tooltip'leri `custom_tooltip` ile geliyor — silinmesi güvenli (doğrulandı). Loc anahtarları yetim kaldı ama zararsız, Faz 4'te yeniden kullanılabilir.
- [x] **Bozuk fikir onarıldı:** `ethnocentrism_idea_7`'nin +2 misyoner / +2 kültürel misyoner bloğu yeniden etkinleştirildi ([`ve_idea_effects.txt`](common/scripted_effects/ve_idea_effects.txt)). Artık 300 puanlık bu fikir gerçekten bir şey veriyor.
- [x] Tooltip loc'u gerçeğe uyduruldu: `ethnocentrism_idea_7_tt` "+2 Missionary and +2 Bureaucrats" → "+2 Missionaries and +2 Cultural Missionaries", 11 dilde (hepsi çevrilmemiş İngilizce kopyaydı; encoding + CRLF korundu).

**Doğrulama yapıldı:** 103 tanımlı = 103 eklenen, tanımsız/eklenmeyen yok, her modifier tam 1× ekleniyor, **cross-group duplikasyon 0**, brace dengesi, kullanılan **136 farklı modifier adının 136'sı vanilla'da doğrulandı**, tüm 103 modifier'ın loc karşılığı mevcut.

**Bu fazda düzeltilen önceki hatalı teşhislerim:** `country_diplomatic_play_maneuvers_add = 25` ve `country_tech_spread_add = 15` aykırı değer sanmıştım — vanilla sırasıyla 20–100 ve 0.2–75 kullanıyor, ikisi de normaldi. Buna karşılık modun **birçok değeri vanilla'nın altındaydı** (yukarıdaki "yükseltilen" listesi), yani sorun sadece fazla güçlü değerler değil, ölçek tutarsızlığıydı.

**Kalan:** oyunda paneli açıp 15 grubun tooltip'lerinin doğru göründüğünü, ethnocentrism idea 7'nin misyoner verdiğini ve hata logunda modifier hatası olmadığını doğrulamak.

**⚠️ Dokunulmayan, incelenmesi gereken:** `ethnocentrism_idea_5_tt` "+0.7% Missionary and Bureaucrat Power" diyor ama effect `ve_missionary_mdf`'i 3 ile çarpıyor. Metin ile davranış uyuşmuyor olabilir; `ve_missionary_mdf`'in ne yaptığı anlaşılmadan değiştirilmedi.

### Faz 3 — Grup yeniden adlandırma ✅ **TAMAMLANDI** *(oyun içi test bekliyor)*

**Kapsam değişikliği:** Kolon taşıma bu fazdan çıkarıldı, **Faz 4'e alındı.** Sebep: grubu kolon arası taşımak GUI'de widget bloklarını taşımak demek ve Faz 4 zaten 5 yeni grup için aynı ameliyatı yapacak — iki kez yapmak yerine bir kez. Faz 3 saf string rename olarak kaldı, mekanik olarak doğrulanabilir. Kolon listesi adları (`adm_ideas`/`dip_ideas` → `prod_ideas`/`soc_ideas`) ve header loc'ları da Faz 4'e taşındı, çünkü grup hâlâ eski listedeyken kolona "Production Ideas" demek yanlış olur.

**Karar (kullanıcı):** kod içi identifier'lar da değiştirildi → **mevcut kayıtlar bozulur**, bilinçli kabul edildi.

Yapılan 7 rename (içeriği yeni ismine zaten uyan gruplar):

| Eski | Yeni |
|---|---|
| `innovative_idea*` | `academic_idea*` |
| `administrative_idea*` | `bureaucratic_idea*` |
| `ethnocentrism_idea*` | `nationalist_idea*` |
| `politics_idea*` | `parliamentary_idea*` |
| `humanist_idea*` | `reformist_idea*` |
| `trade_idea*` | `mercantile_idea*` |
| `militarization_idea*` | `professional_army_idea*` |

Değişmeyen 4: `diplomatic`, `offensive`, `defensive`, `naval`.
Faz 4'e bırakılan 4 (içerik yeniden dağıtımı gerektiriyor): `economic` → Industrialist+Financial, `syndicalism` → Labour+Welfare, `qualification` → Welfare, `imperialist` → Colonial+Extraction.

- [x] **57 dosya, 2076 değişiklik.** Her grup için `<grup>_idea` prefix'i (böylece `_N_mdf`, `_name`, `_completed`, `_N_var`, `_N_tt` ve `flag:` hepsi otomatik kapsandı), `can_go_<grup>`, ve `boost_*_idea_effect` adları.
- [x] Oyuncuya görünen adlar 11 dilde güncellendi ("Innovative Idea" → "Academic Idea" vb.). Değerler zaten çevrilmemiş İngilizce kopyalardı, çeviri sorunu doğmadı.
- [x] Misyoner/kültür tooltip'lerindeki "Ethnocentrism Idea V" referansları da güncellendi ([`ve_religion_l_*.yml`](localization/english/ve_religion_l_english.yml), [`ve_culture_l_*.yml`](localization/english/ve_culture_l_english.yml)).
- [x] `ve_group_ideas.txt` bölüm yorumları yeni isimlere güncellendi.

**⚠️ Yakalanan tuzak:** Grup ikonlarının texture dosya adları `idea_administrative_ideas.dds`, `idea_humanist_ideas.dds`, `idea_trade_ideas.dds` — bunlar `<grup>_idea` + `s` içeriyor. Naive replace bu yolları bozup ikonları kırardı. Regex `<grup>_idea(?!s)` ile korundu; script her dosyada texture yollarının değişmediğini ayrıca assert ediyor. Diskteki `.dds` dosya adları bilinçli olarak eski kaldı (oyuncuya görünmez).

**Doğrulama yapıldı:** eski identifier kalıntısı **0**; 15 grubun hepsi için modifier tanımı = effect'te eklenme sayısı, `can_go_*`, `_completed`, `_name` loc, `flag:`, GUI string'i **tam eşleşiyor**; 12 dokunulan dosyada brace dengesi; texture yolları sağlam ve hepsi diskte mevcut.

**Kalan:** oyunda paneli açıp yeni grup adlarının göründüğünü, fikir satın almanın çalıştığını ve hata logunda tanımsız identifier olmadığını doğrulamak. **Mevcut kayıtlar bozuk — yeni oyun başlatmak gerekir.**

### Faz 4 — Kolonlar + 4 grup yeniden yapılandırma + 5 yeni grup + 2 dışlayan çift

Altı alt adıma bölündü. GUI en sonda **bir kez** 20 grupla kurulacak (iki kez ameliyat etmemek için).

#### ✅ 4a — 4 grubun identifier rename'i — TAMAMLANDI
32 dosya, 1138 değişiklik. `economic`→**industrialist** · `syndicalism`→**labour** · `qualification`→**welfare** · `imperialist`→**colonial**. Faz 3'ün aynı script'i ve `(?!s)` texture koruması kullanıldı.
- Mevcut bir tutarsızlık düzeltildi: imperialist'in modifier loc değerleri "Imperialis**m** Idea" derken `_name` "Imperialis**t** Idea" diyordu; ikisi de "Colonial Idea" oldu.
- Doğrulandı: eski identifier kalıntısı 0, 15 grubun loc adları tutarlı.
- `events/Economic_Idea.txt`'in `industrialist_idea_7_mdf` tetikleyicisi incelendi: "capstone'a sahip = grubu bitirdi" anlamı içerikten bağımsız, repoint gerekmedi.

#### ✅ 4b — 20 grubun tam içerik dağıtımı — TAMAMLANDI
Tek kaynak: `ideas_design.py` içindeki `DESIGN` tablosu → `ve_group_ideas.txt` üretiliyor (`gen_group_ideas.py`). Elle 8 dosya düzenlemek yerine tek kaynaktan üretim, sonraki alt adımlar da aynı tablodan beslenecek.

**Sonuç: 20 satır / 18 seçilebilir yol** (prod 6/6 · soc 7/6 · mil 7/6), **138 modifier tanımı** (140 − nationalist'in 2 effect-tabanlı fikri).

Üreteç şu doğrulamaları kendi içinde yapıyor ve geçmezse yazmıyor:
- yapı (her grup 7 fikir, kolon geçerli, çiftler karşılıklı)
- **cross-group duplikasyon = 0** (160 farklı modifier tipi, hiçbiri iki grupta değil)
- capstone gücü
- **160 modifier adının vanilla'da varlığı** (`goods_output_<mal>_mult` için mal listesinden doğrulama dahil)

Dış bağımlılıklar korundu: `nationalist_idea_2_mdf` conversion+assimilation birlikte ✓ · `naval_idea_4_mdf` invasion efficiency ✓
Doğrulandı: effect/tooltip'te eklenen ama tanımsız modifier **yok**; 5 yeni grubun modifier'ları tanımlı ama henüz bağlanmamış (4c işi).

#### ✅ 4c — 5 yeni grubu sisteme bağla — TAMAMLANDI
30 dosya. Yöntem: her per-grup switch'ten `academic` dalı brace-eşlemeli çıkarılıp grup adı değiştirilerek 5 kopya araya eklendi (`academic` sadık şablon — `nationalist` değil, onun 5/7 fikirleri effect-tabanlı).

| Hedef | Eklenen |
|---|---|
| [`ve_idea_effects.txt`](common/scripted_effects/ve_idea_effects.txt) | 5 × `boost_<grup>_idea_effect` (150 satır/grup) |
| [`ve_idea_tooltip_effects.txt`](common/scripted_effects/ve_idea_tooltip_effects.txt) | 7 switch × 5 = 35 dal |
| [`idea_tooltip_triggers.txt`](common/scripted_triggers/idea_tooltip_triggers.txt) | 7 switch × 5 = 35 dal |
| [`ve_idea.txt`](common/scripted_guis/ve_idea.txt) | 6 switch × 5 = 30 dal |
| [`ve_ai_effects.txt`](common/scripted_effects/ve_ai_effects.txt) | 5 `random_list` girdisi + 5 boost bloğu |
| [`ve_set.txt`](common/scripted_effects/ve_set.txt) | 5 başlangıç değişkeni |
| [`ve_states.txt`](common/history/states/ve_states.txt) | 20 state, **prod/soc/mil** listeleriyle yeniden yazıldı |
| Loc | 11 dil × (5 grup adı + 35 modifier adı) |

Yeni state'ler (vanilla'da doğrulandı, modda kullanılmıyordu): financial→STATE_LOMBARDY · infrastructure→STATE_RHINELAND · extraction→STATE_URAL · mass_conscription→STATE_ILE_DE_FRANCE · war_economy→STATE_RUHR

**Doğrulandı (script'ten bağımsız):** 20 grubun hepsi için modifier tanımı = effect'te eklenme, 6 GUI switch dalı, 7+7 tooltip dalı, 3 AI referansı, `set_ideas`, state, loc adı, 7 modifier loc — **tam eşleşme, eksik yok**. Sarkan referans yok. 20 `boost_*_idea_effect`. Kolon dağılımı prod 6 / soc 7 / mil 7. Brace dengesi ve CRLF korundu.

#### ✅ 4d — GUI yeniden kurulumu — TAMAMLANDI
[`ve_panel_ideas.gui`](gui/ve_panel_ideas.gui) **2552 → 3044 satır.** Her kolonun iki blok dizisi (120×120 grup ikonu + 85 satırlık 45×45 fikir ikonu bloğu) `academic` şablonundan 20 grup için yeniden üretildi.

- Kolon yorumları `#ADM/#DIP` → `#SOC/#PROD`; header anahtarları `ADM_HEADER`/`DIP_HEADER` → `SOC_HEADER` ("Society Ideas") / `PROD_HEADER` ("Production Ideas"), 11 dilde.
- **Doğrulandı:** brace 636/636 · CRLF tutarlı · 40 per-grup blok (20×2) · her grubun tam 2 bloğu var · **GUI'deki gruplar ile state listeleri birebir tutarlı** (SOC 7/7, PROD 6/6, MIL 7/7) · referans verilen tüm texture'lar diskte mevcut · eksik loc anahtarı yok.

**⚠️ Bulunan iki tuzak:** (1) DIP/MIL kolonlarının grup ikonu blokları yorumsuz `widget = {` kullanıyor, ADM'ninkiler `widget = {\t#Comment` — `#` şart koşan regex 10 bloğu kaçırdı. Çözüm: `visible` satırından geriye doğru bir seviye dışarıdaki `widget = {`'i bulan konumlandırıcı. (2) `harvest_gui.py` dosyayı universal-newline ile okuduğu için offset'leri gerçek CRLF byte konumlarıyla uyuşmuyordu ve şablonlar LF olmuştu — 4d konumları binary okunmuş metin üzerinden kendi içinde yeniden hesaplıyor ve şablonları CRLF'e normalize ediyor.

**⚠️ İkonlar placeholder:** 5 yeni grubun 5 grup ikonu + 35 fikir ikonu mevcut havuzdan tematik olarak yeniden kullanıldı. Diskte 15 grup ikonunun tamamı ve 94 fikir ikonunun 88'i zaten kullanımdaydı, yani yeni sanat üretilmedikçe tekrar kaçınılmaz. **Grup ikonları başka gruplarla görsel olarak çakışıyor.** → 4f

#### ✅ 4e — Dışlayan çiftler — TAMAMLANDI *(mekanik olarak; karar 7'nin UI kısmı uygulanamadı, aşağıya bak)*

`nationalist` ⟷ `reformist` · `professional_army` ⟷ `mass_conscription`

- [x] `embrace_idea_group.is_shown`: 4 gruba karşılık gelen `NOT = { has_variable = can_go_<karşıt> }` eklendi. Birini benimsemek diğerini kapatıyor; `cancel_idea` zaten `can_go_<grup>`'u sildiği için iptal edince karşıt yol kendiliğinden açılıyor.
- [x] **Yeni scripted_gui `ve_idea_group_locked`** ([`ve_idea.txt`](common/scripted_guis/ve_idea.txt)) — 20 dalın hepsi açıkça yazıldı (eşleşmeyen `switch` davranışına güvenilmedi; çiftler dışındaki 16 grup `always = no`).
- [x] GUI: cancel butonunun koşulu 3 kolonda `And(Not(embrace), Not(locked))` yapıldı; her kolona `visible = IsShown(ve_idea_group_locked)` olan devre dışı bir **"Path Closed"** butonu eklendi.
- [x] Loc: `ve_idea_locked` + `ve_idea_locked_tt`, 11 dilde.

**⚠️ Neden bu ek scripted_gui gerekli:** paneldeki embrace ve cancel butonları **katı tümleyen** (`IsShown(embrace)` vs `Not(IsShown(embrace))`). Sadece embrace'i engellersem, oyuncu hiç benimsemediği grupta **Cancel butonu** görür. `ve_idea_group_locked` "karşıt yüzünden kilitli" ile "zaten benimsenmiş" durumlarını ayırıyor.

**⛔ Karar 7 (tek satır + benimseme anında yol seçimi) bu mimaride uygulanamaz.**
Satır kimliği `StateRegion.MakeScope.Var('idea_group')`'dan okunuyor — bu **state region üzerinde yaşayan paylaşımlı global** bir değişken, tüm ülkeler için aynı. Britanya nationalist, Fransa reformist seçtiğinde aynı değişkeni çekişirlerdi; seçim ülkeye özel olamaz. Tek satır tasarımı için ya (a) satırın hangi grubu göstereceği ülke değişkenlerinden türetilmeli — yani panelin geri kalanından farklı, yeni bir görünürlük mekanizması ve 2 ek scripted_gui — ya da (b) satır kimliği state region'dan çıkarılıp ülke başına taşınmalı, bu da tüm panelin veri modelini değiştirir. İkisi de ayrı bir iş; şu anki çözüm **iki satır + kilitli olanda "Path Closed"**.

**Doğrulandı:** brace dengesi (ve_idea.txt 1079/1079, GUI 642/642) · CRLF korundu · `ve_idea_group_locked` 20 dal · 4 çiftin karşılıklı dışlaması · GUI'de 6 `ve_idea_group_locked` referansı (3 cancel + 3 locked buton) · 3 "Path Closed" butonu.

#### ⛔ 4f — İkonlar — KULLANICIYA BAĞLI
4d şu anda **placeholder** kullanıyor: 5 yeni grubun grup ikonu ve 35 fikir ikonu mevcut havuzdan yeniden kullanıldı. Diskte 15 grup ikonunun **tamamı** ve 94 fikir ikonunun 88'i zaten kullanımdaydı, yani tekrar kaçınılmazdı. Sonuç: yeni grupların **grup ikonları başka gruplarla görsel olarak çakışıyor** (financial↔industrialist, infrastructure↔colonial, extraction↔labour, mass_conscription↔offensive, war_economy↔defensive).

Mevcut ikonlar EU4'ten alınmış görünüyor (`prestige.dds`, `innovativeness_gain.dds`, `tolerance_heathen.dds` gibi adlar). Vanilla Victoria 3 ikonları stilistik olarak uyumsuz olurdu.

**Özgün `.dds` üretilemiyor.** Seçenekler: (a) 5 grup ikonu + 35 fikir ikonunu kullanıcı hazırlar/temin eder, dosya adları verilirse GUI'ye bağlanır; (b) placeholder'lar kalır (fonksiyonel, görsel olarak tekrarlı); (c) EU4 ikon setinden uygun olanlar mod'a kopyalanır — kullanıcının o dosyalara erişimi varsa.

Placeholder atamaları `faz4d_gui.py` içindeki `PLACEHOLDER` tablosunda; gerçek ikonlar gelince o tablo güncellenip script yeniden çalıştırılır.

**Faz 3'ten devralınan ek işler (4d'ye dahil edildi):**
- [ ] Kolon listeleri: `adm_ideas`/`dip_ideas` → `prod_ideas`/`soc_ideas` ([`ve_states.txt`](common/history/states/ve_states.txt) + [`ve_panel_ideas.gui`](gui/ve_panel_ideas.gui)'deki `GetGlobalList`)
- [ ] Header loc: `ADM_HEADER`/`DIP_HEADER` → `PROD_HEADER`/`SOC_HEADER` ("Production Ideas" / "Society Ideas")
- [ ] **Grupları hedef kolonlarına taşı** — GUI'de widget bloklarını kolon vbox'ları arasında taşımak gerekiyor. Hedef: prod = mercantile, industrialist, financial, infrastructure, extraction, labour · soc = academic, bureaucratic, parliamentary, welfare, diplomatic, nationalist, reformist · mil = offensive, defensive, naval, professional_army, colonial, war_economy, mass_conscription
- [ ] **4 grubu ismiyle+içeriğiyle yeniden yapılandır:** `economic` → Industrialist (inşaat/sanayi) + Financial (vergi/kredi) · `syndicalism` → Labour (sendika/ücret) + Welfare (ölüm/doğum/SoL) · `qualification` → içeriği Academic ve Welfare'e dağıt · `imperialist` → Colonial (sömürge) + Extraction (hammadde)

**Asıl Faz 4 işleri:**
- [ ] [`ve_group_ideas.txt`](common/static_modifiers/ve_group_ideas.txt): 5 yeni grup × 7 modifier + 20 ambition modifier
- [ ] [`ve_idea_effects.txt`](common/scripted_effects/ve_idea_effects.txt): 5 yeni `boost_*_idea_effect` (Faz 1 sonrası çok daha kısa)
- [ ] [`ve_idea.txt`](common/scripted_guis/ve_idea.txt): `embrace`/`boost`/`cancel` switch'lerine 5 yeni dal + dışlayan çift kontrolü (§4.6)
- [ ] [`ve_panel_ideas.gui`](gui/ve_panel_ideas.gui): 5 yeni widget bloğu + dışlayan çift için tek-satır/yol-seçimi UI (**karar 7**)
- [ ] [`ve_states.txt`](common/history/states/ve_states.txt): 5 yeni state ataması
- [ ] [`ve_ai_effects.txt`](common/scripted_effects/ve_ai_effects.txt): AI'nın yeni grupları değerlendirmesi
- [ ] İkonlar → `gfx/interface/ve_ideas/` (vanilla/mod kaynaklarından mod-local kopya; özgün çizim yok)
- [ ] Loc: 5 grup adı + 35 fikir adı + 20 ambition adı/tooltip

### Faz 5 — Ekonomi + kapılar + ambition ✅ **TAMAMLANDI**

#### ✅ 5a — Ambition (grup tamamlama ödülü)
20 × `<grup>_ambition_mdf`. Her biri **kendi grubunun zaten sahip olduğu** bir modifier tipini güçlü değerle tekrarlıyor — böylece grup kimliğini pekiştiriyor ve cross-group duplikasyon doğmuyor. Üreteç bunu ayrıca denetliyor (`ambition denetimi`).
- 7. fikir alındığında ekleniyor (`<grup>_idea_completed` ile aynı yerde), `cancel_idea`'da kaldırılıyor.
- Loc: 11 dilde `<grup>_ambition_mdf` = "<Grup> Ambition".
- Tanım 20 / eklenen 20 / kaldırılan 20 / loc 20 — tam eşleşme.

#### ✅ 5b — Age kapıları
🔒Age 2: labour, welfare, nationalist, reformist, mass_conscription, colonial · 🔒Age 3: war_economy

- `embrace_idea_group.is_shown`'a `has_global_variable = age_N_started_trigger` eklendi. **`ve_age_N_started` kullanılmadı** — o global sonraki çağ başlarken siliniyor, yani grup yeniden kilitlenirdi (§4.5 tuzağı).
- AI'nın kapılı grubu erken seçmemesi için `ve_ai_choose_idea`'nın `random_list` girdilerine de aynı şart eklendi (7 grup).
- **Yeni scripted_gui `ve_idea_group_age_locked`** + GUI'de devre dışı **"Not Yet Available"** butonu. 4e'deki aynı tuzak: embrace gizlenince cancel görünür, o yüzden cancel artık `And(Not(embrace), And(Not(pair_locked), Not(age_locked)))`.
- Loc: `ve_idea_age_locked` + `ve_idea_age_locked_tt`, 11 dilde.

#### ✅ 5c — Kademeli maliyet
**200 / 250 / 300 / 375 / 450 / 550 / 675 = 2800/grup** (eskiden 300 × 7 = 2100).

Motor bir değişkeni flag adından arayamadığı için `idea_cost` hangi grubu/seviyeyi satın aldığını bilemez. Çözüm iki taraflı:
- **Ödeme:** her branch kendi seviyesini bildiği için `ve_idea_purchase_common` yerine `ve_idea_purchase_1..7` çağrılıyor (140 branch dönüştürüldü, her seviye 20 çağrı).
- **Karşılanabilirlik:** `boost_idea_group.is_valid` ve `ve_ai_boost_idea` grup bazında switch'lendiği için `var:<grup>_idea` okunabiliyor. **Parametreli scripted trigger** `ve_idea_affordable = { GROUP = <grup> }` mevcut seviyeyi sonraki maliyete eşliyor (Vic3 `$PARAM$` destekliyor, vanilla'da doğrulandı).
- `idea_cost` / `idea_cost_trigger` tanımlı kaldı (alert hâlâ trigger'ı kullanıyor); trigger en ucuz kademeye (**200**) ayarlandı, yani "bir şey alabilirsin" anlamına geliyor.
- **Yan iş:** `diplomatic`/`offensive`/`defensive`/`naval` adları hiç değişmediği için effect'leri kısaltılmış kalmıştı (`boost_dip/off/def/nav_idea_effect`). 3 dosyada normalize edildi → artık 20 grubun hepsi `boost_<grup>_idea_effect`.

**Denge sonucu:** 8 grubu bitirmek 22.400 puan, 100 yıllık bütçe ~18.000 → **~4.400 açık**, yani seçtiğin 8 grubun ancak ~6.4'ünü bitirebiliyorsun. Hedeflenen gerilim oluştu.

#### ✅ 5d — `national_idea_pool` kalibrasyonu — İKİNCİ TURDA TAMAMLANDI
[`ve_national_ideas.txt`](common/scripted_guis/ve_national_ideas.txt) eşikleri
**3/6/9/12/15/18/21** olarak korundu. Ancak her satın alınan fikrin +1 vermesi,
artan maliyet eğrisiyle birlikte çok sayıda gruptan ucuz ilk fikirleri toplama
teşviki yaratıyordu. `national_idea_pool` artık her satın alma ve iptalden sonra
tamamlanmış gruplardan yeniden hesaplanıyor: **bir tamamlanmış grup = 3 puan =
bir ulusal fikir.** Yarım gruplar ulusal ilerleme sağlamıyor.

**Doğrulama (script'ten bağımsız):** 20 grubun hepsi için ambition tanımı/eklenme/kaldırma/loc, `boost_<grup>_idea_effect` varlığı, seviye 1..7 çağrıları (brace eşlemeli), `ve_idea_affordable` is_valid'de 1 + AI'da 1, age şartı — **tam eşleşme, sorunlu grup yok.** Maliyet eğrisi tanımlarla birebir. Kalıntı yok: `ve_idea_purchase_common` 0, `idea_cost_trigger` 0, kısaltılmış effect adı 0. GUI'de 4 buton tipi × 3 kolon.

> Not: `ve_ai_uses_age_bonuses` içindeki 3 `ve_age_N_started` kullanımı **doğru ve dokunulmadı** — "şu an hangi çağdayız" sorusu birbirini dışlayan global gerektiriyor, kümülatif `_trigger` değil.

## 6c. Faz 6 — Agrarian eklendi (Production'a dışlayan çift)

Kullanıcı, önceki oturumdan sonra dosyaları elle geliştirdi (özellikle `cancel_idea`'ya bir onay
popup'ı ve `ve_idea_group_ambition` adında ambition tooltip'i için yeni bir scripted_gui
eklendi, ayrıca Extraction'ın 7. fikrine elle bir Age 3 kapısı konuldu). Bu oturumda **Production**
kolonuna 6. dışlayan çift eklendi: eski "Extraction" grubu tarım+madencilik+petrolü tek grupta
topluyordu; bu artık iki kimliğe bölündü.

- **Extraction** (madencilik/petrol/kauçuk) — mining, resource discovery/depletion, rubber,
  iron, sulfur, oil capstone. İçerik korunan yapı, sadece tarım kaldırıldı.
- **Agrarian** (YENİ, `extraction` ile dışlayan çift) — agriculture, ranching/plantations,
  food security, grain/meat/fruit output, subsistence arable land. State: **STATE_PUNJAB**
  (vanilla'da doğrulandı, modda kullanılmıyordu).

**Sonuç: Production 6 satır/6 seçilebilir → 7 satır/6 seçilebilir**, Society ve Military'yle
aynı desene oturdu. **Toplam 21 grup, 18 seçilebilir yol** değişmedi (yeni satır bir çiftin
ikinci yarısı, ekstra seçenek değil).

### Uygulama sırasında çıkan iki bulgu

1. **Dosyalar önceki oturumdan sonra elle değişmişti.** `academic` şablonunu kopyalarken beklenenden
   fazla switch bulundu (6 değil 8) — sebebi kullanıcının eklediği `ve_idea_group_ambition`
   scripted_gui'si. Anchor'ı buna göre güncelledim; ayrıca Faz5c'nin `idea_cost_trigger` → 
   `ve_idea_affordable` değişimini AI dosyasında yeniden bulmam gerekti (aynı sebepten, script
   pattern'i eski yapıya göre yazılmıştı).
2. **Ambition ekle/kaldır adımlarını gereksiz yere tekrar yazmışım.** `academic` şablonu zaten
   Faz 5a'nın eklediği ambition grant/removal mantığını içeriyordu — klonlama sırasında otomatik
   geliyor. Elle yazdığım tekrarı fark edip sildim.
3. **5 dosyada satır sonu "karışık" çıktı ama bu benim değişikliğim değil** — `tr -dc` ile disk
   üzerinde doğrulandı: dosyalar zaten kullanıcının elle düzenlemelerinden dolayı karışıktı. Katı
   kontrolü bilgilendirici uyarıya çevirdim; asıl doğruluk ölçütü olan brace dengesi zaten %100.

**Doğrulama (script'ten bağımsız):** 21 grup tanımlı, cross-group duplikasyon 0, embrace/locked
dallarının ikisi de karşılıklı pair mantığı taşıyor, state ataması doğru, **GUI'nin PROD kolonu
tam 7 grup içeriyor ve her biri 2 blok (grup+fikir ikonu)**, loc mevcut. Brace: mdf 166/166,
effects 1072/1072, guis 1304/1304, gui 695/695.

**Not (dokunulmadı, bilgi amaçlı):** Extraction'ın capstone'undaki elle eklenmiş
`has_global_variable = age_3_started_trigger` şartı `boost_extraction_idea_effect`'te var ama
`boost_idea_group.is_valid`'deki karşılanabilirlik kontrolü (`ve_idea_affordable`) bu age şartını
bilmiyor — teorik olarak oyuncu Age 3 öncesi "afford edilebilir" görüp tıklayabilir ve etkisiz bir
tıklama olabilir. Bu satırlara ben dokunmadım (kullanıcının kendi eklemesi), sadece not ediyorum.

## 6b. İlk oyun içi test sonucu (log ayıklaması)

Mod oyunda **açıldı ve fikir paneli yüklendi.** Log'da bu refactor'un ürettiği **hiçbir hata yok.**

### Log'un doğruladığı şeyler (yokluğuyla)
- `ve_religion.txt:2182` "Value of wrong type ... type 'none'" spam'i **gitti** → oturumun başındaki `ve_set.txt` misyoner değişken prefix düzeltmesi çalıştı.
- `ve_idea_purchase_1..7`, `ve_idea_affordable` (**parametreli scripted trigger sözdizimi doğru**), `ve_idea_group_locked`, `ve_idea_group_age_locked` → parse hatası yok.
- 20 grup, 138 fikir modifier'ı, 20 ambition, 11 dildeki loc → eksik modifier / eksik loc anahtarı hatası yok.
- Yeniden kurulan GUI kolon bölgesi (satır 694+) → **hiç hata yok**, eksik texture yok.

### Düzeltilen (bu refactor'dan önce de vardı)
- **`ve_set.txt` `set_national_idea`** — `NOR` bloğu var olmayan ülkelerle karşılaştırma yapıyordu (`c:SGF`, `c:NGF`, `c:PRU`), her ülke için tekrarlanan "Invalid right side during comparison 'c'" hatası üretiyordu (~66 satır log). 12 tag'in hepsi `AND = { exists = c:X  this = c:X }` ile korundu — bu dosyanın 788+ satırlarında yazarın kendi kullandığı kalıp. Git ile doğrulandı: hata commit'li sürümde de vardı (535-537), benim 4c eklemelerim satır numaralarını 54 kaydırmış. Tüm dosya tarandı, korumasız `this = c:` kalmadı.

### Dokunulmadı — bu refactor'la ilgisi yok
- `ve_panel_ideas.gui` satır 120–621 "Property 'margin' not handled" (10 widget): `widget` tipi `margin` desteklemiyor, değer yok sayılıyor. Git ile doğrulandı, commit'li sürümde birebir aynı; benim ilk değişikliğim 694. satırda. **Bilinçli dokunulmadı:** `widget` → `vbox` yapmak margin'i etkinleştirip mevcut düzeni değiştirirdi, panel şu an düzgün görünüyor.
- `ve_panel_culture.gui:195`, `ve_panel_age_bonusses.gui:445` "Widget cannot have a position in a layout" — başka paneller.
- `topbar.gui:497` "Callback property 'onclick' not handled".
- Tüm `pdx_persistent_reader` hataları — başka modların oyun kuralları (elgar, lepsius, pbi, tgr, spy agencies, governors…) ve kayıt uyumu. Bu modla ilgisi yok.

### Hâlâ oyunda doğrulanmayı bekleyen
Log temiz olması bunların çalıştığını **kanıtlamaz** — sadece parse edildiklerini gösterir:
- Kademeli maliyetin gerçekten 200/250/.../675 tahsil ettiği (bir grubu satın alıp puanı izle)
- `ve_idea_affordable`'ın doğru seviyede engellediği
- Ambition'ın 7. fikirde eklendiği, iptalde kaldırıldığı
- Age kapıları: 1871 ve 1906'ya ilerleyip 7 kapılı grubun açıldığı, "Not Yet Available" → embrace geçişi
- Dışlayan çiftler: birini benimseyince diğerinde "Path Closed" göründüğü, iptalde yeniden açıldığı
- SOC/MIL kolonlarının 7 satırla taşmadığı

## 7. Doğrulanmış modifier sözlüğü

Aşağıdakilerin motorda var olduğu bu oturumda doğrulandı (`00_modifier_types.txt` ve vanilla kullanımı üzerinden). Yeni oturum bunları tekrar araştırmasın.

**Building group throughput** (dinamik üretilir, `00_modifier_types.txt`'te aranmaz):
`agriculture, arts, extraction, fishing, government, heavy_industry, infrastructure, light_industry, logging, manufacturing, military, military_industry, mining, oil_extraction, plantations, ranching, rubber, service, whaling` → `building_group_bg_<X>_throughput_add`
Ayrıca `_unincorporated_` varyantları: `logging, manufacturing, mining, plantations, rubber`

**İnşaat / şirket:** `state_construction_mult`, `country_max_weekly_construction_progress_add`, `country_max_companies_add`, `country_company_throughput_bonus_add`, `country_company_construction_efficiency_bonus_add`, `state_capitalists_investment_pool_efficiency_mult`, `state_farmers_...`, `state_shopkeepers_...`

**Havuz `_mult`'ları (flat yerine bunlar kullanılacak):** `country_bureaucracy_mult`, `country_authority_mult`, `country_influence_mult`, `country_prestige_mult`, `country_tech_spread_mult`

**İnovasyon:** `country_weekly_innovation_add`, `country_weekly_innovation_max_add`, `country_weekly_innovation_mult`

**Altyapı:** `state_infrastructure_mult`, `state_infrastructure_from_population_mult`, `state_urbanization_per_level_mult` *(negatif = bonus)*, `state_urbanization_mult`

**Demografi / refah:** `state_mortality_mult`, `state_mortality_wealth_mult`, `state_mortality_turmoil_mult`, `state_non_homeland_mortality_mult`, `state_birth_rate_mult`, `state_working_adult_ratio_add`, `state_dependent_wage_add/_mult`, `state_welfare_payments_add/_mult`, `state_political_strength_from_welfare_mult`, `state_expected_sol_from_literacy`, `state_literacy_growth_add`, `state_pop_pol_str_mult`, `state_dependent_political_participation_add`

**Göç:** `state_migration_pull_add/_mult`, `state_migration_pull_unincorporated_mult`, `state_migration_quota_mult`, `country_mass_migration_attraction_mult`

**Radikal / loyalist:** `state_radicalism_increases_*_mult`, `state_loyalism_increases_*_mult`, `country_loyalists_from_legitimacy_mult`, `country_radicals_from_legitimacy_mult`, `country_radicals_from_conquest_mult`, `state_radicals_from_political_movements_mult`, `state_loyalists_from_political_movements_mult`
*(`*` = `violent_hostility`, `cultural_erasure`, `open_prejudice`, `second_rate_citizen`, `full_acceptance`)*

**Sömürge:** `state_colony_growth_speed_mult`, `state_colony_growth_creation_factor`, `state_non_homeland_colony_growth_speed_mult`

**Celp:** `state_conscription_rate_add/_mult`, `state_building_conscription_center_max_level_add`

**Bilinen YOK'lar (kullanılmayacak):** tarife modifier'ları (`country_tariff_*`), `country_trade_route_cost_mult`, `state_market_access_price_impact_mult`, `country_mobilization_option_cost_mult`, `country_expenses_mult`

---

## 8. Riskler ve dikkat noktaları

| Risk | Önlem |
|---|---|
| **Age global'i silinme tuzağı** — `ve_age_2_started` Age 3'te siliniyor | Kapılarda **sadece** `age_N_started_trigger` kullan (§4.5) |
| **Çalışan yapı bozulması** (kullanıcının açık şartı) | Fazları sırayla, her fazdan sonra oyunda test. Faz 1 ve 2 davranış-nötr olmalı |
| **`national_idea_pool` regresyonu** | Faz 5'te kademe sayısını sayıp eşikleri yeniden ayarla |
| **11 dilde loc kırılması** | Faz 3'te anahtar adı değişince tüm dillerde eşle; encoding/satır sonu (CRLF + UTF-8 BOM) korunsun |
| **Var olmayan modifier adı** | §5'teki `⚠️` işaretlileri ve tüm yeni adları `00_modifier_types.txt` + vanilla kullanımına karşı doğrula |
| **Duplikasyonun geri gelmesi** | Faz 2 ve 4 sonunda tüm `ve_group_ideas.txt` üzerinde modifier-adı frekans denetimi çalıştır |
| **GUI'de elle yazılmış grup blokları** | Her grup için `visible = EqualTo_string(...)` string'i ayrı; grup adı değişince hepsi güncellenmeli (Faz 3) |

## 9. Kurallar (CLAUDE.md'den, hatırlatma)

- `C:\Program Files (x86)\Steam\steamapps\common\Victoria 3\game` **salt okunur.** Oraya asla yazma/kopyalama.
- Yeni tanımlayıcılar `ve_` prefix'li olmalı.
- Yıkıcı git komutu kullanma (`reset --hard`, `checkout --` vb.).
- Oyun içi doğrulama yapılamadıysa "çalışıyor" denmez, açıkça belirtilir.
