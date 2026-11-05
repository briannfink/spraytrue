# TankMix Pro (v2.8.0)


## Unified EPA + Washington State (WSDA) product search (v2.8.0)
Lookup and Products › **Add product** search both EPA (live APPRIL/PPLS) and a bundled Washington State Dept of Agriculture registration index in one box — no database picker.
- **WSDA coverage in the bundled index:** spray adjuvants and 25(b) minimum-risk pesticides from the public [WAPRS search](https://fortress.wa.gov/agr/pisces/WSDASearch/Default) (WALTR fertilizers optional via refresh). Section 3 (EPA) pesticides registered in WA can be added with `tools/update_wsda.py --section3` (large / slow).
- **Merged rows:** when a WSDA Section 3 record shares an EPA Reg. No. with an EPA hit, one row shows **EPA** + **WSDA** badges and the detail view adds a Washington registration block (status, expiry, View WA label PDF → WSDA hosted file, not re-hosted).
- **WSDA-only rows:** adjuvants, 25(b), fertilizers, etc. open a WSDA detail (name, registrant, WA reg no., type, agents, status/expiry, View WA label / WSDA page). Save to My products tags the entry with `waReg` / `wsdaId` (rates entered by you). Dedupe by WA reg no. (and EPA reg when present).
- **Data approach:** WSDA has no public REST API and no CORS for browser calls from GitHub Pages. The app ships `data/wsda-products.json` (lazy-fetched, SW-cached). Refresh: `python3 tools/update_wsda.py` (polite ~1 req/s HTML pagination of the public search; CSV export postback is broken without ASP.NET client scripts). Optional weekly GitHub Action: `.github/workflows/update-wsda.yml`.
- **Storage:** additive only (`waReg`, `wsdaId`, `wsdaDb`, `source` on library entries). Live and preview share `tm.*`.

## Products EPA lookup + duplicate guard (v2.7.1)
- The **Products** tab has an **Add EPA product** search at the top (same EPA/APPRIL + PPLS search as Lookup, without crop/pest filters). Results open the same detail view; **Save to My products** is there, and rows already saved show **In My products**.
- Saving to My products no longer creates a second copy: EPA products match by normalized Reg. No.; custom products match by trimmed case-insensitive name. A toast says **Already in My products**. Existing stored duplicates are left alone (no migration). Backup import skips incoming items that match an existing EPA/name (same-ID still replaces).

## Tools + Products tabs (v2.7)
- **Order** and **Sprayer** are combined under one bottom-bar tab called **Tools** (where Sprayer used to be). A Sprayer | Order segmented control switches between the two; both features work as before. `showTab("order")` / `showTab("cal")` and anything that jumped to those tabs still land on the right Tools sub-view.
- **My products** moves out of Settings › Saved into its own **Products** tab (where Order used to be). EPA and custom products, tags, search, add/edit/delete stay. Settings › Saved keeps saved mixes and backup, plus a link to the Products tab.
- On the Products tab, tapping a product opens its detail (Lookup-style EPA detail for EPA products; an equivalent detail with edit for custom products). A plain tap no longer adds to the mix; use **Add to mix** on the detail (or Quick add on Mix) for that.
- Bottom bar is still six tabs: Mix · Products · Tools · Lookup · Weather · Settings. Tools/Products tabs add no new storage keys; Weather Underground adds `tm.wu` (additive). Preview and live keep sharing `tm.*`.


## Carrier amount per load (v2.6)
The app now shows how much carrier to put in the tank, not just the product amounts.
- **Carrier = load volume − volume of all products in that load.** Liquid products (and % v/v adjuvants) count at their volume. Dry products count only when a **bulk density (lb/gal)** is entered on the product card (the density box now always shows for dry products); the estimate is lb ÷ lb/gal. Without a density a dry product is treated as negligible and listed as "Dry products not subtracted".
- **Mix tab:** a line under Tank plan ("Carrier to add: X per full tank · Y partial · Z total") and a **Carrier to add** card under Products with per full tank, partial (last) tank and total job, to 0.1 gal or 0.1 L. With a liquid-fertilizer carrier it also shows a Water / fertilizer table (e.g. Water 144.1 gal + UAN 28% 144.2 gal); the rows are rounded so they add up to the carrier total. If the products are more than the tank holds, it warns and shows 0 carrier.
- The fertilizer carrier now fills the room left after liquids **and** dry products with a density (before, only liquids). Mixes with no dry density are unchanged.
- **Order tab:** step 1 says the carrier per load and lists about half of it to put in first (water first when the carrier is part water); the last step "Fill to final volume with the rest of the carrier/water" lists the rest and the fill-to volume. The WALES/APPLES product groups between them are unchanged.
- **Print / share:** carrier rows (one per component, plus Total carrier for fertilizer) in the product table, the notes, and the carrier amounts in the mixing order and the share text.
- **Spray log:** records get an optional `carrierAmt` text (computed for the record's acres), shown in the form, detail, print, text share and a new **Carrier amounts** CSV column after Carrier. v2.5 ignores it and keeps it.
- Saved mixes need nothing new: carrier is computed from the saved tank, rate, area and products. No new storage keys.


## Weather Underground personal weather stations (v2.7.1)
Settings › Weather source › **Weather Underground PWS station(s)** opens the WU panel (alongside Tempest).
- **Connect:** paste a free API key (PWS owners: [wunderground.com › Member › API Keys](https://www.wunderground.com/member/api-keys)) and a station ID (e.g. `KXXCITY12`), then **Connect**. Optional label. The key can be shared across stations or different per station.
- **Several stations / accounts:** **＋ Add another WU station**. Stations merge into one list with a **WU** badge; hide / ★ default / ✎ rename work like Tempest.
- **Weather tab:** with WU active, a station picker replaces the place row. Current obs come from `api.weather.com/v2/pws/observations/current` (units=e); the 12-hour outlook comes from Open-Meteo at the station. Source badge shows **WU** (vs **Tempest**).
- **Log a spray › Fill from local weather:** nearest enabled WU station to the field pin (≤ ~10 mi, fresh ≤ 15 min); otherwise Open-Meteo at the pin with a reason. Record source looks like `WU · Home (1.2 mi) · 6:52a`.
- **Key privacy:** keys live only in `tm.wu` and are sent only to `api.weather.com`. Left out of backups unless **Include Tempest / Weather Underground API keys** is ticked.
- **CORS:** `api.weather.com` returns `Access-Control-Allow-Origin: *` (including on 401), so browser use from GitHub Pages works.

## WeatherFlow Tempest stations (v2.5)
Settings › Weather source › **WeatherFlow Tempest station(s)** opens the Tempest panel.
- **Connect:** paste a personal access token (password box with 👁 show/hide; optional account name) and tap **Connect**. The app calls `GET https://swd.weatherflow.com/swd/rest/stations?token=…` and lists the stations. Create the token at **tempestwx.com › Settings › Data Authorizations › Create Token** (per WeatherFlow's API docs).
- **Several accounts:** **＋ Add another Tempest account** connects more tokens. All stations go into one list, each labelled with its account; a station seen by two tokens is listed once. **Remove** deletes an account and its token from this device.
- **Per station:** tick to use or hide, ★ to make it the default, ✎ to rename it in this app only (the Tempest name stays shown). Each row shows its last reading time ("2 min ago"), "stale" after 15 minutes, or "no recent readings (offline?)". **↻ Check readings** re-lists every account and reads each station.
- **Errors:** a bad token (401), no network, a token with no stations, and a 404 station are all reported in the panel; nothing is saved for a failed connect.
- **Weather tab:** with Tempest active, a station picker replaces the place row. Current conditions come from the station (`GET …/observations/station/{id}`), with the reading age, a stale warning after 15 minutes, plus Delta T, lull and last-hour rain tiles. The 12-hour outlook, sunrise/sunset and the inversion hint (model 80 m − 2 m temperature difference) come from Open-Meteo at the station's spot. If the station can't be read (401, offline, no readings), the whole reading falls back to Open-Meteo at the station's location and says why.
- **Log a spray › Fill from local weather:** uses the enabled station nearest the field pin (haversine, any account), else the default station. If the nearest is more than 10 mi away, stale, or fails, it uses Open-Meteo at the field pin (or the station's spot when there's no pin) and says why. The **Tempest station** picker in the form lets you pick a station yourself (then distance and staleness are only noted). The record stores `wx.source` like `Tempest · Home (1.2 mi) · 6:52a`, plus `wx.station {id,name,mi}`, `wx.obsTs` and `wx.deltaTC`.
- **Units:** Tempest REST observations are always metric; the app converts °C→°F, m/s→mph (×2.23694), mm→in. Delta T stays in °C (2–8 ideal; flags under 2, over 8, over 10).
- **Token privacy:** tokens are stored only in `tm.tempest` on this device and are sent only to `swd.weatherflow.com` (as the documented `?token=` parameter, with no cookies or referrer). They never go into settings, records, CSV, print or share text. **Export backup** includes station names/choices but leaves tokens out unless **Include Tempest access tokens** is ticked. Import adds accounts from a backup that has them (no duplicates).
- **CORS:** `swd.weatherflow.com` answers with `Access-Control-Allow-Origin: *` (also on 401 replies and preflight), so it works from GitHub Pages and from `file://`.
- `better_forecast` is not used (Open-Meteo gives the 80 m temperature for the inversion hint and keeps the outlook the same for both sources).


## Clear mix (v2.4)
The **✕ Clear** button in the Mix tab's "Sprayer & field" heading resets the form to a new blank mix (no products, empty name, default tank/carrier/field size for your units, no fertilizer carrier). It also resets `tm.current`, so a reload stays blank. An **Undo** toast shows for 8 seconds and restores the previous mix exactly. Settings, saved mixes, My products, fields, logs and calibration are not touched. No new storage keys.

Two ways to use it:
- **Single file:** open `index.html` directly (double-click, email it, or copy it to a phone). Everything is inside it.
- **Installable app (PWA):** host the `dist/` folder on any static HTTPS server, open it, and choose "Add to Home Screen" or "Install". It works offline after the first visit. Live EPA search also needs a web address, because EPA blocks pages opened as `file://`.

Published on GitHub Pages (repo briannfink/tankmix): live root https://briannfink.github.io/tankmix/ and review copy https://briannfink.github.io/tankmix/preview/.

## Tabs (bottom bar)
- Mix: tank calculator, products and costs, water or liquid-fertilizer carrier
- Products: My products (EPA and custom) plus an EPA search to add products; tap opens detail, not add-to-mix
- Tools: Sprayer (calibration and nozzles) and Order (WALES/APPLES + jar test)
- Lookup: EPA search with crop/pest filter
- Weather: local spray conditions, shared with the spray-record form
- Settings: a hub containing
  - **Saved** (saved mixes, backup and import; link to Products)
  - **Logs** (spray records)
  - app settings (units, theme, weather source)

## Grower, farm and weather in the spray log (v2.3)
- **Grower** and **Farm** sit above Field and Crop in the Log a spray form (new and edit). Both are optional.
  - They suggest names you've used before, from past records and saved fields. The farm list shows that grower's farms first.
  - A new record starts with the grower and farm from your last record, or from the saved field when the mix name matches one.
  - Saving a record with **Save as a field** checked stores the grower and farm on the field. A blank grower or farm never erases what the field already has.
  - Picking a saved field, or typing its name, fills in its grower and farm. You can also change them under Logs > Saved fields > (field) > **Grower / farm…**.
- Grower and farm show in the record list ("Grower › Farm") and the record detail. In print, they appear in the record heading and in their own rows. The text share includes them too.
- The CSV has new **Grower** and **Farm** columns right after Date/time. Backups carry them on records and saved fields.
- The search box also matches grower and farm. Once any record has a grower, a **grower/farm filter** appears, and CSV and Print follow it.
- **Fill from local weather** never sends you to the Weather tab. It picks a location in this order:
  1. The record's field pin or coordinates. This gives weather at the field, even when the Weather tab is set somewhere else. A repeat tap within 15 minutes reuses the same reading.
  2. The Weather tab's location.
  3. Your phone's location.
  4. If location access is blocked or unavailable, a **Town, ZIP, or lat, lon** box opens right in the form (Open-Meteo geocoding).
  - The button shows "Finding your location…" or "Getting weather…" while it works. Errors appear inline in the weather section.
  - If no weather location was set, the spot found (field pin, phone location or typed place) becomes the Weather tab's location. An existing one is never replaced.

## Field location map (v2.2)
The Log a spray form (new and edit) has a **Field location** section:
- Satellite (Esri World Imagery with road and place labels) or Street (OpenStreetMap). Attribution is shown on the map.
- Tap the map to drop a pin, then drag it to fine-tune. You can also type or paste coordinates in decimal (`42.0135, -93.7412`), with N/S/E/W letters, in DMS or degrees-minutes (`42°00'48.6"N 93°44'28.3"W`), or as a Google/Apple Maps link. The pin and the box stay in sync.
- **Use my location** uses the phone's GPS.
- The map starts at the field you used last, then your weather location, then the whole US.
- **Draw boundary** (optional): tap the field corners. The app shows the area in acres and can copy it into Acres sprayed. You can undo, clear, or drag a corner.
- **Save as a field** keeps the name, pin and boundary. Saved fields show in a dropdown on later logs, and typing a saved field's name fills them in too. You can manage saved fields under Logs > Saved fields.
- The location is saved with the record. It shows as 📍 in the list, and the record detail has a small map and an Open in Maps link (`https://maps.google.com/?q=lat,lon`).
- Print shows the coordinates, the DMS form, the link, a boundary sketch and the corner list. It doesn't include map imagery.
- The CSV adds these columns: Latitude, Longitude, Map link, Mapped boundary acres, and Boundary corners.
- Backups include saved fields.
- Leaflet 1.9.4 is bundled into the file (`vendor/`; the build checks its SRI hashes), so the map controls work offline and from `file://`. Map imagery needs a connection. When offline, the map says so, and typed coordinates still save. The service worker does not intercept or cache cross-origin tile requests.

## Custom products (v2.2)
Go to the **Products** tab > **Add custom product** to add products without an EPA Reg. No., such as adjuvants, fertilizers, micronutrients and drift agents. Each one has a name, manufacturer, category, liquid or dry, a default rate (unit and basis), density, mixing-order type (filled in from the category), price, and active ingredients or notes.

**Quick add** on the Mix tab is now a searchable picker. It lists My products tagged EPA or Custom, filterable, plus the generic adjuvants. Picking one fills its default rate, unit, type and price. A generic or free-typed product shows **Save to My products**. You can edit, duplicate or delete products from the ⋯ menu. Backup and import include custom products.

## Saved data (localStorage, shared by live and preview)
The keys are `tm.settings`, `tm.mixes`, `tm.library`, `tm.log`, `tm.current`, `tm.epaCache`, and `tm.wxLast`. v2.8.0 adds no new `tm.*` keys (library entries may gain `waReg`/`wsdaId`). v2.7.1 adds `tm.wu` (Weather Underground PWS accounts/keys/prefs, same shape idea as `tm.tempest`). v2.6 adds no keys; log records may get a `carrierAmt` string and products may carry a `density` for dry products (the existing field). v2.5 adds `tm.tempest` (`{accounts:[{id,name,token,stations}], prefs:{stationId:{hidden,alias}}, def, sel, seen}`); records may get `wx.station`/`wx.obsTs`/`wx.deltaTC`, and `settings.wxSrc` may be `"tempest"` (v2.4 ignores all of these and falls back to Open-Meteo, which test7 checks). v2.2 adds `tm.fields` (saved fields) and `tm.schema` (2). v2.3 adds no keys and leaves the schema at 2. Records and saved fields may get optional `grower`/`farm` strings, and settings may get `lastGrower`/`lastFarm`. v2.2 ignores these and keeps them when it edits a record or field, which the tests check.

Migration only adds fields: library items get `custom`/`mfr`/`cat`/`phys`, and log records may get `loc {lat, lon, boundary, bAcres, fieldId}`. No keys are renamed or removed, so v2.1 still reads everything.

## Printing (v2.1)
Print opens a full-page print view of the mix sheet or spray records. It has these buttons:
- **Print** calls `window.print()` directly from the tap.
- **Share / Save PDF** uses the Web Share API (a printable `.html` file, or text if the browser can't share files).
- **Download** saves a standalone printable `.html` file.

iPhone and iPad home-screen apps ignore `window.print()`. The app detects standalone mode (`navigator.standalone` or `display-mode: standalone`) and points to Share instead. If no print dialog opens within 1.5 s on any platform, the same hint appears.

## Updates and preview
- The `dist/sw.js` cache name is `tankmix-<version>-<build hash>`. Pages load network-first, so a new deploy shows up on the next launch. A new worker activates immediately, and an open page shows "A new version is ready. Tap to refresh".
- `preview/` is a review copy meant for `<site>/preview/`. It has no manifest, no service worker and a "Preview" badge, and the live worker ignores `/preview/`. It shares the same site storage, so it sees the same saved mixes and logs.

## Files
- `src/part1.html`: CSS and markup
- `src/part2.js`: units, calc engine, fertilizer carrier, calibration math, nozzle table
- `src/part3.js`: Mix, Order and Saved UI
- `src/part4.js`: EPA lookup and print
- `src/part5.js`: Sprayer tab
- `src/part6.js`: weather sources and spray-condition flags
- `src/part7.js`: spray log and app init
- `src/part8.js`: field map (coordinate parsing, Leaflet map, boundary/acres, saved fields)
- `src/part9.js`: custom products, My products list, Quick add picker, data migration
- `src/part10.js`: WeatherFlow Tempest (accounts, stations, REST calls, unit conversion, nearest station, Settings panel)
- `vendor/leaflet.js`, `vendor/leaflet.css`: Leaflet 1.9.4 (BSD-2), inlined by the build
- `tools/build.py`: builds `index.html` and `dist/` (manifest, icons, `sw.js`)
- `tools/build_dataset.py`: refreshes `tools/epa-data.json` from EPA's live API. This offline snapshot covers 54 products, including EPA's site and pest lists, dictionary-encoded.
- `tools/test.js` (v1), `tools/test2.js` (v2) and `tools/test3.js` (v2.1), `tools/test4.js` (v2.2: coordinates, map, fields, custom products, migration, offline, SW/tiles, preview) and `tools/test5.js` (v2.3: grower/farm, fill-from-weather without a Weather-tab location, denied-location fallback, and v2.2 reading v2.3 data via `_test/v22/index.html`), `tools/test6.js` (v2.4 Clear mix) and `tools/test7.js` (v2.5 Tempest, fully mocked API: 401/network/no stations, multi-account, units, nearest station, fallback, token privacy, v2.4 via `_test/v24/index.html` reading v2.5 data), `tools/test8.js` (v2.6 carrier per load: calc, dry density, fertilizer split, over-volume, metric, Order steps, print, share text, log/CSV, saved mix, v2.5 via `_test/v25/index.html` reading v2.6 data): plus `tools/test9.js` (v2.7 Tools/Products) and `tools/test10.js` (v2.7.1 WU PWS): Playwright tests. Run `python3 -m http.server 8765` in this folder, then run each with node. They need `playwright-core` and Chrome. `test3.js` uses `_test/v20/index.html`, a v2.0 build used for the saved-data compatibility check; it is not part of the deploy.

## EPA data sources (all public, nothing hand-entered)
- **APPRIL** product listing (search, crop/site and pest filter): `https://ordspub.epa.gov/ords/pesticides/cswu/apprilapi/?q={json}&limit=100&offset=n`. The app searches by product name, alternate brand name, or active ingredient. It sends crop and pest as `$instr` filters, then re-checks the crop client-side with a strict prefix match, because EPA's own match is loose ("Corn" also hits "Acorn Squash"). Results are active registrations by default; "include inactive" widens the search.
- **PPLS** detail and labels: `.../cswu/ppls/{regno}` and `https://www3.epa.gov/pesticides/chem_search/ppls/{pdffile}`. This provides the full site and pest lists shown on the product page.
- **CORS:** EPA allows any http(s) origin and returns 403 for `file://` pages. Opened as a file, the app searches the embedded snapshot plus products you looked up before.
- An EPA site or pest listing means the registration covers that use. **Rates, REI, PHI, timing and restrictions are only on the label.**

## Weather
- Built in: **Open-Meteo** (free, no key, CORS-open, so it works from `file://` too). It provides the current conditions and 12 hourly values of wind, gusts, temperature, RH, rain chance, and temperature at 2 m and 80 m (used as an inversion hint). Times are local to the location.
- Location: 📍 browser geolocation, or a typed ZIP, town, or `lat, lon` (Open-Meteo geocoding). Browsers often block geolocation on `file://`.
- Flags are general guidelines only: wind under 3 or over 10 mph, gusts, possible inversion, 85 °F and above (caution) or 90 °F and above (poor), RH under 40 %, and rain chance. **The product label takes precedence.** In the spray log, every reading can be typed in or overridden by hand.

### Tempest source (v2.5)
Registered in `src/part10.js` with the same `WX.register` shape as Open-Meteo, plus `usable()` (at least one station turned on). See "WeatherFlow Tempest stations (v2.5)" above.

## Calibration math
- GPA = GPM × 5940 ÷ (mph × W). W is the nozzle spacing in inches; for band spraying, W is the band width.
- 1/128-acre course = 4083.75 ÷ W ft. Fluid ounces caught in the drive time = GPA.
- mph = ft ÷ s × 3600/5280. GPM₂ = GPM₁ × √(P₂/P₁).
- Nozzle sizes use ISO flat-fan rated flow at 40 psi. Droplet size is not estimated; it depends on the tip model, so use the manufacturer's chart.
