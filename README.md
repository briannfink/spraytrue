# SprayTrue (v2.17.0 — live; published Nov 13, 2026)

## v2.17.0 — Shapefile field boundaries + NDVI, Grower › Farm › Field, job names, Title Case (live)

- **Fields › Saved fields › ⬆ Import shapefile boundaries**: pick a .zip or the loose .shp/.shx/.dbf/.prj(/.cpg) files. Reprojected in the browser from the .prj: WGS84/NAD83 lat-long, UTM (any zone, NAD83 or WGS84), Transverse Mercator, Lambert Conformal Conic (WA State Plane North/South, US feet or metres), Web Mercator. Lat/long without a .prj is accepted with a note; NAD27 shows a warning. Polygons, multipart polygons and holes; one field per feature, name from FIELD_NAME/NAME/FIELD/… (editable before saving), farm/grower attributes if present. Acres are geodesic (WGS84) from the original shape.
- Saved fields keep using the existing per-record Supabase sync (`tm.fields`). Boundaries over 1,200 points are simplified (Douglas-Peucker) to keep sync light. Single-ring fields store `boundary` as before; multipart/holed fields add `shape`. Same-name imports update the existing field (id, spray links, grower/farm kept).
- Field dialog: satellite map with the boundary, recent sprays on the field, and **🛰 NDVI satellite images**.
- **NDVI**: Sentinel-2 L2A from Element 84 Earth Search (free, no key, CORS open). The browser reads only the Cloud-Optimized GeoTIFF tiles over the field with HTTP range requests. Field-specific clear % from the SCL band; NDVI clipped to the boundary, cloud/shadow hatched, legend with % of the field in each class, mean / low 10% / median / high 10%. Older dates can be picked.
- Updates: opening NDVI checks for new dates (at most every 6 h; ↻ forces). On app open, fields that already used NDVI are re-checked once a day (skipped offline or with Data Saver) and show “🛰 New image” when a newer clear date appears. Scene lists are cached in `tm.ndviIndex` (device-only, not synced); images in IndexedDB (last ~6 dates per field) for offline viewing.
- Data: re-check ≈ 2 KB catalog + ≈ 5–60 KB per new date; first NDVI open ≈ 20 KB catalog + ~10 small classification tiles + one image (~2.5–3 MB, more if the field straddles satellite tile edges).
- **Fields tab is a Grower › Farm › Field drill-down**: each step is one compact row — short label, dropdown, and small square **＋** (add) and **✎** (edit) icon buttons (42 px, labelled for screen readers): **Grower**; once chosen, **Farm** (that grower's farms); once chosen, **Field** (that grower + farm). The chosen field shows its summary (acres, shapefile, 🛰 New image), **📝 Log spray**, **🛰 NDVI**, **🗺 Map** and every spray record for it, newest first (records link by saved field id, then by name). One option auto-selects; the last grower/farm/field is remembered on the device (`tankmix.fieldsNav.v1`, not synced). Fields saved without a grower/farm appear under **(No grower)** / **(No farm)**. **⬆ Import shapefile boundaries** is under the steps (presets the chosen grower/farm) and inside Add field. **📂 Unassigned spray records** (no matching saved field) is below the selected field; **Search all spray records** (search, grower/farm filter, CSV, print) stays at the bottom, listing results while searching or after **Show all**.
- **＋ / ✎ for grower and farm** open one small inline panel under that row only when tapped (tap again, ✕ or Esc closes): add a name, or rename — carried to that grower's farms, its fields and the grower/farm text on spray records (renaming onto an existing name asks to merge) — and a small **🗑 Delete** inside the edit panel, which first confirms with how many farms, fields and spray records are affected. Deleting a grower removes its farms and fields; deleting a farm removes its fields. **Spray records are never deleted**: they stay as they were and are reachable in Unassigned and the search. **✎ on Field** opens the field details (map, NDVI, grower/farm, **✏️ Rename, map & boundary** — pin and drawn boundary; redrawing replaces a multi-part shapefile outline; renaming keeps records that used the old name attached — and **🗑 Delete field**, same record-safe confirmation).
- **Growers & farms list (`tm.growers`)**: an explicit saved list so an empty grower or farm can exist, seeded from the grower/farm names already on saved fields and spray records (names you delete are remembered so they aren't re-created from old records; adding the name again restores it). It syncs through the existing key sync as one `tm.*` value (newest copy wins) — no Supabase schema change. Included in backups.
- **Grower / farm on saved fields**: **＋ Add field**, the field details screen and the shapefile import preview (each boundary, plus *Grower / farm for all* when there are several) have **Grower** and **Farm** selectors listing growers and farms already used on spray records or saved fields, with **＋ New grower…** / **＋ New farm…** to type a new one. Farms list only the chosen grower's farms (all farms when no grower is chosen); picking a farm with one known grower fills the grower. Field details saves on change (replaces the old prompts). Values are the same plain `grower`/`farm` strings on the `tm.fields` record, so they sync as before. Pickers list the saved Growers & farms; Add field and import preset the grower/farm chosen in the drill-down.
- **Title Case labels**: the app's own buttons, labels, headings, section titles, tab names, placeholders, dropdown options, dialog titles and status labels now capitalize each word (e.g. **Save Mix**, **Tank Amounts →**, **Cost & Planning Notes**, **Job Name**, **Choose a Grower…**, **＋ New Field…**, **📍 Use My Location**, **Acres Sprayed**, **Add Custom Product**, **Rename Station**). Small words (a, an, the, of, to, in, on, for, and, or, by, per, with…) stay lowercase unless first; units and abbreviations stay as they were (gal, fl oz, ac, mph, GPA, GPM, psi, NDVI, EPA, CSV, e.g.). Nothing you type is changed — grower/farm/field/job/crop names, notes and products are shown and saved exactly as entered (no CSS text-transform). Kept as is on purpose: help paragraphs, toasts and confirmation messages (sentence case), mixing-step instructions, generic adjuvant product names (they become product names in a mix), Leaflet's own map tooltips, and the **CSV header columns** (unchanged, including “Job name”, so spreadsheet imports keep working). Option values and internal ids are unchanged.
- **Field location: no coordinate entry**: the Latitude, Longitude box, its 🔎 find button and the coordinate help text are removed from the spray record location section. Location comes from tapping/dragging the pin, **📍 Use My Location**, a picked saved field, or a drawn boundary. Pin status reads **📍 Pin Set · Open in Maps ↗ · Clear Pin**. The spray record and **＋ Add Field** / ✏️ Edit Field maps are now **square** (same width, `aspect-ratio: 1/1`) and Leaflet re-measures the map whenever its box resizes. `tools/test29.js` (25 assertions) covers both changes; legacy browser suites test4/5/7/10 still reference `#lgCoord` and are not runnable here.
- **Spray record Grower › Farm › Field picker**: the record form's Grower, Farm and Field are compact rows of real dropdowns (they work on iPhone and Android) built from the saved Growers & farms list and saved fields — farms filter to the grower, fields to the grower/farm (all fields when none is chosen). Picking a field fills its grower and farm, links the record by field id and loads its pin, boundary and acres. **＋ New grower… / ＋ New farm… / ＋ New field…** type a name that isn't saved (typing a saved field's name links it). Presets: a field's 📝 Log spray uses that field; ＋ New spray record and Mix › Log Spray Record use the Fields tab selection (field, else grower/farm), else the mix name if it is a saved field, else the last grower/farm used. The mix name now only prefills Job name, not Field. Edit record shows the linked field (or the unsaved name as typed text). The old “Saved fields” dropdown inside the map box and the grower/farm suggestion lists are gone.
- **Job name on spray records**: the spray record form (Mix › Log Spray Record and a field's 📝 Log spray) starts with **Job name**, prefilled from the current mix name and editable; it's editable on existing records too (Edit) and kept in unfinished drafts. Stored as `job` on the record, so it syncs with the existing per-record sync (JSON value, no schema change). Record lists (selected field, Unassigned, search results) and record/menu titles read **Job name · Crop**; older records without one use the mix name, else the date. The field, grower and farm move to a detail line; the date stays on the secondary line. Job name is searchable, shown in the record view, print and text share, and added as a **Job name** column at the end of the CSV (existing columns unchanged).
- **Mix › Cost & planning notes** (the collapsible section with **Cost** and the planning notes) moved from Tank amounts to the main Mix page, directly above Log Spray Record. Same cost math and notes; Tank amounts no longer shows it.
- **Mix › Log Spray Record** (was “Log this spray” under Tank amounts, then “📝 Log Application”; no icon) is now at the bottom of the mix editor, below Products; it starts a spray record from the current mix exactly as before. Tank amounts no longer has a log button.
- **Mix**: the Edit mix / Tank amounts switch is gone. The editor shows directly with one full-width **Tank amounts →** button at the top; Tank amounts has **← Back to mix** at the top and still has **⛶ Full screen · check off**.
- Note: legacy Playwright suites (test2–test7) that expected `#logList` to list every record by default now need a search or **Show all** first; they are not runnable in this environment. JSDOM suite `tools/test25.js` covers the new layout.
- Tab bar: “Logs” is now **Fields** (🗺️) and sits before Tools: Mix · Products · Fields · Tools · Weather · Settings. Internal view id (`log`) and storage keys unchanged.
- Tests: `tools/test24.js` (143 offline assertions; `NET=1` adds a live Sentinel-2 fetch cross-checked against rasterio/shapely), fixtures from `tools/make_shp_fixtures.py` (pyproj reference values), `tools/ndvi_crosscheck.py`.

## v2.16.0 — Full-screen mixing mode (preview)

- **Mix › Tank amounts** has a new **⛶ Full screen · check off** button that opens a full-screen checklist for the selected scope (full tank, last partial tank, or whole-job totals, clearly labeled).
- Very large, forced black-on-white text for sunlight and E Ink. No color or animation is needed: checked rows show a filled ✓ box, strike-through and dotted border. Big tap targets, with a two-column layout in wide landscape.
- Water/carrier row(s) first, then every product with the same amounts and formatting as Tank amounts (gallon products as whole gal + fl oz). Rows follow the Tools mixing sequence, without any steps or instructions.
- "N of M added" progress readout, **Reset checks**, and **✕ Close**. Escape and the Back button also close it.
- Checks are saved on this device per mix + scope (`tm.mixChecks`, not synced) and reset automatically when the mix or any amount changes. Rows with a missing label rate are shown but can't be checked.
- Keeps the screen awake with the Wake Lock API where the browser supports it; otherwise it does nothing.
- No calculation changes. Tests: `tools/test23.js` (42 assertions).

## v2.15.2 — jug-friendly Tank product quantities (preview only)

- Preview: https://briannfink.github.io/spraytrue/preview/ . Build/cache identity: `spraytrue-2.15.2-8ea1373f` (preview deliberately has no service worker). **Live stays v2.15.1**, cache `spraytrue-2.15.1-d05952d5`. Source backed up first to `/tmp/tankmix-app-v2151`.
- Liquid **product** quantities that would show gallons in Tank amounts now use whole US gallons plus remaining US fluid ounces: `2.5 gal → 2 gal 64 fl oz`, `1.25 gal → 1 gal 32 fl oz`, `21.25 gal → 21 gal 32 fl oz`. Whole gallons omit zero ounces. Existing subgallon ounce readouts are unchanged (e.g. `0.625 gal → 80 fl oz`).
- The gallon/ounce split rounds only the display to 0.1 fl oz, with carry at 128 fl oz (e.g. `1 gal + 127.95 fl oz → 2 gal`), using the original unrounded calculation rather than the old rounded decimal-gallon string. Gallon and ounce groups can wrap separately on narrow phones without splitting their units.
- Same formatter for full tank, last partial and whole-job product quantities. Dry products, non-gallon/metric readouts, carrier/water/fertilizer carrier volumes, stored rates, actual calculations, Tools mixing order, logs, print/PDF and sync are unchanged. No dependencies, data or Supabase changes.
- `tools/test22.js`: **69** new unit/assembled-DOM assertions covering exact/subgallon/carry/precision boundaries, all load scopes, preserved dry/metric/carrier values, unchanged stored calculations and original decimal-gallon print/PDF output. Existing `test20.js` **109**, `test21.js` **32**, and `test19.js` **91** assertions also pass; **11** offline WSDA fixture tests pass. Build and JS syntax checks pass.
- No browser automation or screenshots produced. Native phone layout (including two-part quantity wrapping) still needs actual browser/iPhone validation.

## v2.15.1 — quantities only in Tank amounts (approved live)

- Preview: https://briannfink.github.io/spraytrue/preview/ . Build ID/cache: `spraytrue-2.15.1-d05952d5` (preview has no service worker). Live remains **v2.14.0**, cache `spraytrue-2.14.0-e7b65abe`. Backup: `/tmp/tankmix-app-v2150`.
- Brian requested no mixing order in Tank amounts. Removed its numbered/grouped steps, fill/agitation/top-off instructions and duplicated mixing-guide control. Tank amounts now shows a plain product list in mix-list order, with full/partial/job quantities, carrier components, selected spray volume and WA identity. Mixing order and jar-test functionality remain under **Tools › Order**, unchanged; print/PDF and calculation code are untouched.
- Missing-rate, over-volume, dry-density and fertilizer compatibility/density warnings remain visible, along with the independent label caution or whole-job-not-one-tank warning.
- Verification: `test21.js` **32** focused assertions; `test20.js` **109** Mix assertions; `test19.js` **91** reliability/sync assertions; **11** offline WSDA fixtures. Build and syntax checks pass. All JavaScript runs use an isolated non-browser DOM, mocked network/auth; no real account data touched.
- No browser automation or screenshots produced. Actual desktop/iPhone visual validation remains outstanding. Source and preview deployment only; no live or Supabase changes.

## v2.15.0 — initial Mix cleanup (historical preview; superseded by v2.15.1)

- Preview: https://briannfink.github.io/spraytrue/preview/ . Candidate build ID/cache: `spraytrue-2.15.0-e378947c`. Preview deliberately has no manifest or service worker. **Live must remain v2.14.0**, cache `spraytrue-2.14.0-e7b65abe`. Source backed up first to `/tmp/tankmix-app-v2140`.
- **Before:** saved-job summary, loading summary, setup, product editors with three calculated tiles each, tank-plan tiles and a separate carrier table all appeared in one long stream. Save/Print also appeared on unrelated tabs.
- **After:** a compact Saved Mixes dropdown and **New mix** start the workflow; no repeated current-job/count/date paragraph. **Edit mix** contains numbered sprayer/field setup and products/label rates. Optional price/density fields fold away, retaining their open state during edits. **Add product…** uses the existing saved-product/search picker; **Enter manually** preserves direct entry.
- **Tank amounts** is a separate field-use view. One selector shows **Full tank**, **Last partial tank**, or clearly marked **Whole job totals — not one tank**. Each product appears once, in the existing mixing sequence. Per-load instructions, agitation, selected final fill volume, label priority, missing-rate, overflow, dry-density and fertilizer compatibility warnings stay visible. The full guide/jar test remains reachable in Tools. Cost/planning notes are optional rather than another permanent card of totals.
- Clean saved mixes open in Tank amounts; unfinished drafts resume in Edit. **Use tank amounts** advances without saving and moves keyboard focus below the sticky header/status. Mode changes do not modify the mix. Carrier-only water/fertilizer jobs, partial-only jobs, exact full loads, metric units, costs, fertilizer weights/nutrients, logs, Clear/Undo and saved-mix management remain available.
- **New mix** confirms before discarding unfinished work, including setup-only changes, and retains Undo. Existing saved-picker discard confirmation and unsaved-change header remain. **Save mix / Print mix** are shown only on Mix. Printing/PDF still contain full/partial/job amounts regardless of the currently selected amount view.
- Scope: Mix markup/UI helpers, header action visibility and version only. No Supabase administrative calls, migrations or data changes. Authentication, record-sync code, `tm.*` formats, WSDA data/updater and PWA assets/workflow are unchanged.

### v2.15 verification / desktop handoff

- `tools/test20.js`: **109 assertions passed** in the assembled app's isolated non-browser DOM: chooser/new/undo, both modes, focused forward action, optional-field state, dirty/reload/saved behavior, all amount views, correct order/no duplicate product rows, full/partial/carrier-only/fertilizer/dry/metric cases, warning/instruction visibility, WA metadata, actual PDF bytes and log routing.
- `tools/test19.js`: **91 assertions passed**, retaining v2.14 reliability, cross-device record merge/conflicts/retries/account isolation, CSV and PDF checks. Network/auth are mocked; no real account data or emails touched.
- WSDA offline fixtures: **11 tests passed**. Build and all JavaScript syntax checks passed. No scrape or WSDA workflow run.
- Commands on this box: `NODE_PATH=/workspace/agent-tools/spraytrue-review-work/node_modules node tools/test20.js`, then the same command for `tools/test19.js`; `python3 -m unittest discover -s tools -p test_wsda.py -v`.
- Existing browser suites through `test18.js` retained, with intentional Mix navigation/quantity/header/confirmation assertions updated and syntax-checked, **not executed**. No Shell browser automation, actual browser renders, or substitute screenshots were made for v2.15.
- **Actual browser/device validation needed:** 390px and 320px layouts (light/dark), native saved/amount dropdowns, sticky header/status and forward scroll/focus with the keyboard, mode switching while editing, New mix cancel/confirm/Undo, full versus partial versus planning-total clarity, long product names, optional price/density controls, inline mixing warnings, print/share PDF and real installed-PWA offline/reload behavior. Run retained browser suites using the permitted desktop testing setup; a real iPhone pass is still needed.

## v2.14.0 — field reliability and safer sync (approved live)

- Historical v2.14 release: now approved live at https://briannfink.github.io/spraytrue/ , cache `spraytrue-2.14.0-e7b65abe`. Original source backup: `/tmp/tankmix-app-v2130`. The current preview-only release is described above.
- **1 — Weather:** stale/missing readings show **Conditions unknown**, never a green Good/within-guidelines message. Station freshness uses its existing station threshold; model snapshots expire after 60 minutes. The display rechecks each minute and on focus/reconnect. Labels still take precedence.
- **2 — Saved state:** edited saved jobs show **Unsaved changes** until explicitly saved. Comparison normalizes legacy fertilizer defaults and ignores object-property order.
- **3 — WA traceability:** new spray-record product snapshots retain `waReg`, `wsdaId`, `wsdaDb`, and `source`; WSDA products are not classified as Custom. Screen/print/PDF/text sharing show WA registration; CSV adds WA reg nos and Product sources at the end, preserving all previous column positions. JSON backups retain additive fields. Previously saved logs that already discarded these fields cannot be reconstructed reliably; they are not silently rewritten.
- **4 — Record sync:** library products, saved mixes, spray records and fields now sync separately with server revisions, tombstones, durable retry receipts and conflict copies. A stale edit or edit-versus-delete keeps a recoverable copy rather than overwriting the other version. Open mix/library/log editors remember their edit-start revision. First contact canonicalizes duplicate product/identical mix IDs and retains distinct data. Settings, weather accounts and the current draft still use the existing key-level transport.
- **5 — Loading this tank:** an immediately available full/last-partial selector shows carrier and product amounts in mixing sequence. Prepared-job setup collapses automatically; Edit setup / rates opens it. Detailed editable product cards, full mixing-order instructions, calculations, cost and Clear/Undo remain available.
- **6 — Always-visible status:** every tab shows local-only / waiting / syncing / synced / offline / attention-needed status. Offline readiness explains that installed calculations, saved data and PDF creation work offline; fresh weather, new EPA searches, map imagery and label links need a connection. Download needed labels to Files in advance. Preview deliberately has no worker/install cache.
- **7 — Log drafts:** unfinished forms autosave on input/change and page hide, restore after reopening, and preserve typed location controls and notes. Cancel/replacing a draft requires confirmation; saving clears it. Drafts are device-only, separated by account under `tankmix.logDraft.v1.<owner>`.
- **8 — WSDA updates:** every selected scrape must have a positive advertised total matching the unique received count. Failed/short/empty refreshes raise an error before writing anything. Successful category replacements are atomic, retain untouched categories, and record per-category verified dates/counts and a conservative last-successful date. The workflow runs offline fixture tests first and reports failures in its run summary. No full scrape was run for this release; bundled data is unchanged. The search shows last successful update and flags old/unverified snapshots.
- **9 — One product search:** Products contains the full original Lookup engine, including crop/site, typed site, pest, inactive and pagination functionality. Advanced filters are collapsible. Tools › Lookup and `showTab('lookup')` route directly to the same Products search with filters expanded. Search products replaces Search EPA. In My products indicators and full detail/library actions remain.
- **10 — Clear action scope:** global buttons now say Save mix and Print mix; log printing remains separate.

### Additive Supabase migration / compatibility

Project `tankmix` (`qcwneqqfiyuouokklnpg`) gained `public.user_records` (owner/collection/record ID, JSON value, revision UUID, server timestamp, deleted flag), `public.user_record_ops` (owner-scoped idempotency receipts), and security-invoker `public.spraytrue_records_sync(jsonb)`. Both tables have authenticated-owner-only RLS and no anonymous grants. The RPC serializes account writes, compares revision IDs, and retains conflict copies. Migration: `supabase/migrations/20261108223254_spraytrue_record_sync.sql`.

**Existing `user_data` rows, policies and `tankmix_sync` were NOT modified.** The first v2.14 sync transaction copies the four legacy collections once, without deleting/rewriting their original rows. v2.13 can still use its old transport but cannot address the new record store. Use v2.14 or newer on all working devices after approval: edits/deletes to existing records made only in an old version after migration do not overwrite the new store.

Because live and preview share localStorage, v2.14 also keeps owner-separated private collection caches. If an old tab replaces a shared array, v2.14 restores its canonical collection, imports only genuinely unseen additions (not known tombstones), and retains a bounded private older-app recovery archive. Settings offers **Download older-app recovery snapshots** when needed. These files require manual review, not blind import. Extra local recovery copies consume storage; export a backup if storage warnings appear. `tm.*` arrays and backup marker `app:"tankmix-pro"` remain compatible. No service-role key, password, auth user or existing synced data was changed. Weather API keys retain their previous private-account sync behavior.

### Verification and limitations

- `tools/test19.js`: 91 assertions over the assembled app in an isolated non-browser DOM, covering all 10 items, actual PDF bytes, two-device merging/conflicts/retry/in-flight edits, first-contact dedupe, older-tab overwrite protection, full auth/sync coordination and account isolation. Auth/network are mocked; no real email/password actions.
- `python3 -m unittest discover -s tools -p test_wsda.py -v`: 11 offline fixture tests, including incomplete/duplicate/empty rejection and byte-for-byte preservation of the last-good file on failure.
- Supabase transaction tests: bootstrap, conflict-copy preservation, retry idempotence, tombstone-versus-edit, cross-owner read/write denial. All test writes rolled back; no production records edited.
- Existing browser suites `tools/test.js` through `test18.js` retained and updated for canonical search, collapsible setup and mocked record endpoints; all syntax-checked. They have **not been rerun** in this session: no browser delegate is available, and Shell-driven browser automation is not permitted. Real Safari/iPhone install, offline update, auth recovery and Share PDF still need a browser/device pass. New static phone-width renders are clearly labeled as non-browser renders, not screenshots proving browser layout.
- Static render artifacts (not browser screenshots): `/workspace/tankmix-app/screenshot-v214-1-mix.png`, `screenshot-v214-2-weather.png`, `screenshot-v214-3-products.png`, `screenshot-v214-4-log-draft.png`. Generated from the new build with sample data using `tools/render-phone-static.js` and WeasyPrint, with document-renderer layout accommodations; they do not verify native control/layout behavior.
- Confirmed before deployment: Brian retains all 12 legacy keys (21 products, 6 mixes, 0 logs, 0 fields); both new tables remain empty after rolled-back integration tests.
- Security advisors: no new table/RLS/function issues. The existing **Leaked Password Protection Disabled** Auth warning remains; see https://supabase.com/docs/guides/auth/password-security#password-strength-and-leaked-password-protection . No plan or Auth settings changed.

## SprayTrue rename (v2.13.0 — approved live)

- Live: https://briannfink.github.io/spraytrue/ ; preview: https://briannfink.github.io/spraytrue/preview/ . Deploy repository: `briannfink/spraytrue`; existing deployment checkout stays `/tmp/tm`, remote `https://github.com/briannfink/spraytrue.git`.
- Editable source stays **`/workspace/tankmix-app`** (intentionally not renamed); pre-rename backup: **`/tmp/tankmix-app-v2121`**. Build with `python3 tools/build.py`. This repository contains built output and the standalone WSDA updater, not the editable source.
- Display/title/header, apple-mobile title, manifest name/short_name, print/PDF/log-share branding and download filenames now use **SprayTrue**. Icons are unlettered tank/drop artwork, so they remain valid. Install start URL and scope are relative `./`; cache prefix is `spraytrue-2.13.0-<hash>`.
- **No storage migration:** every `tm.*` key, `tankmix.*` session/recovery/archive key, RPC `tankmix_sync`, and backup marker `app:"tankmix-pro"` remains unchanged. New backup/PDF/CSV filenames use `spraytrue-`; old backup files still import normally.
- `https://briannfink.github.io/tankmix/` is a separate small public redirect repository. Root, preview and 404 pages preserve the full path suffix, query and fragment (including Supabase recovery tokens). Its `/tankmix/sw.js` retirement worker skips waiting, clears offline CacheStorage, claims old-scope clients, unregisters itself and navigates only `/tankmix/` clients to matching `/spraytrue/` paths. It NEVER clears localStorage or user data. Source for these files is `tools/legacy-redirect/`.
- Same browser/profile origin stays **https://briannfink.github.io**, so saved mixes/products/logs/settings appear at the new path without export/import. Test18 verifies raw saved data through an actual old-worker upgrade and the new app's offline registration. Different browsers/profiles and some iOS standalone containers are separate stores: sign in/sync or back up from the original container before removing its icon. Old installed apps must reconnect once to receive the redirect worker; add the new address to the home screen if the old name/scope remains.
- **Manual Supabase change:** in project `tankmix` → Authentication → URL Configuration, save Site URL **https://briannfink.github.io/spraytrue/** and add redirect URLs **https://briannfink.github.io/spraytrue/**, **https://briannfink.github.io/spraytrue/index.html**, **https://briannfink.github.io/spraytrue/preview/** and **https://briannfink.github.io/spraytrue/preview/index.html**. Keep old `/tankmix/` redirect allowlist entries temporarily for already-issued emails. The app derives signup/recovery URLs from its current location. Do not change Supabase project ID, URL, publishable key, auth users, tables or RPC for this rename; the internal project name may remain `tankmix`.
- **Email branding:** update any custom SMTP sender display name and Confirm signup / Reset Password email-template headings to **SprayTrue**. Prefer the default `{{ .ConfirmationURL }}` link instead of hardcoded old app addresses. A verified SMTP sender address/domain does not need changing just because the app name changes. Default email limits and Confirm email settings are unchanged.
- Update bookmarks/shared links and any external documentation to the new address. Reusing the original repo name for redirects means old Git repository URLs now refer to the redirect repo; update other developer clones/remotes and external integrations to `briannfink/spraytrue`.
- **WSDA automation repaired:** existing workflow referred to a nonexistent `tools/build.py` in the built-output repo and omitted live-root dataset staging. The revised weekly/manual workflow needs no app source: it runs the updater, copies `data/wsda-products.json` to published root and preview paths, stages the dataset copies and a recomputed service-worker cache hash, and explicitly publishes a Pages artifact (bot pushes alone do not trigger Pages). It has the necessary contents/Pages/OIDC permissions. Its checkout uses the current repository automatically and the updater User-Agent now references SprayTrue. No full hours-long WSDA scrape is required merely to rename the app.
- Regression: `tools/test18.js` covers rebrand, manifest, real old-worker upgrade, new offline cache, same-origin saved data, old backups, PDF branding, and root/preview/404 Auth-fragment redirects. All other tests continue to run.


## Email + password Account / Sync (v2.12.1, retained in v2.13.0)

Settings → **Account / Sync** now offers **email + password**, **Sign in**, **Create account**, and **Forgot password?**. The magic-link/email-code UI and OTP requests are removed. Normal password sign-in works across devices without sending email or depending on redirects. Existing v2.12.0 sessions/data remain compatible.

- **Already used email-link login and have no password:** do NOT create another account. Enter your existing email and use **Forgot password?** once. Open the newest recovery email, set/confirm a password in SprayTrue, then use that email/password on your Mac, iPhone, or installed PWA. If Create account gets an existing/obfuscated user response, the app directs you to Forgot password? instead of claiming the old password was changed.
- **Recovery:** the `type=recovery` implicit redirect is verified with Supabase and opens Settings → Set a new password. It strips the URL tokens, preserves the recovery session device-only across reloads, and does not sync/upload device data until a password is successfully set and private-sync consent is checked. Cancel clears the temporary recovery session. Old/expired links show an actionable error.
- **Change password:** while signed in, choose Change password and enter current/new/confirmed password. Passwords go only to Supabase Auth over HTTPS; never into localStorage, exports or synced rows. Inputs clear after submit/cancel. Server password-strength and recent-authentication policies still apply.
- **Create account:** use at least 8 characters. With Confirm email enabled, signup sends one confirmation email; confirm it before signing in. If confirmation is disabled, successful signup signs in directly. Existing accounts and their synced rows are never deleted/recreated by the app.
- Wrong password, unconfirmed email, duplicate signup and rate limits have clear messages. Signup/recovery requests have a 60-second local cooldown; Supabase's project-wide email quota can still require an hour. There is no automatic resend/retry of email.
- Brian's existing user `0e791c96-c773-432f-b864-ee09850a013b` was checked with a read-only count: **0 user_data rows** at implementation time. No auth user or cloud rows were changed. This does not affect locally saved data.
- Security advisor currently reports **Leaked Password Protection Disabled** (an Auth warning, not an RLS/table exposure). Supabase documents this feature as **Pro plan and above**; the project is Free. No plan/settings changes were made. Use a strong unique password; enable protection if upgrading. Reference: https://supabase.com/docs/guides/auth/password-security#password-strength-and-leaked-password-protection
- Backup before this work: `/tmp/tankmix-app-v2120`. That version was preview-tested before approval; v2.13.0 is approved for live deployment at /spraytrue/.

### Required dashboard setup for recovery/signup emails

1. Project **tankmix → Authentication → URL Configuration**: set and SAVE **Site URL** to `https://briannfink.github.io/spraytrue/` (NOT localhost:3000).
2. Add/save exact **Redirect URLs**:
   - `https://briannfink.github.io/spraytrue/preview/`
   - `https://briannfink.github.io/spraytrue/preview/index.html`
   - `https://briannfink.github.io/spraytrue/`
   - `https://briannfink.github.io/spraytrue/index.html`
3. Leave Email enabled under **Authentication → Sign In / Providers → Email**. Keep the normal `{{ .ConfirmationURL }}` link in **Reset Password** and **Confirm signup** templates; no OTP template edits are needed for this version.
4. The default Supabase email service usually permits only project-organization member addresses and **2 emails/hour project-wide**, shared by signup/recovery. Wait for the quota to reset before Brian requests one recovery email. Configure **Authentication → SMTP Settings** for dependable production delivery/higher email limits. Password sign-in itself sends no email.
5. **Confirm email:** leaving it ON is recommended, especially for public/production use; it proves email ownership. Turning it OFF can reduce emails for new signups in a private personal app, but permits unverified addresses. It is optional, not required, and does NOT set a password on Brian's existing account or remove the recovery-email requirement for that passwordless account. No auth settings were changed here.

Recovery/confirmation links can be opened in another browser/device because this is the client-only implicit flow (no PKCE device binding). After setting the password there, sign into the installed PWA with email/password; Safari and installed-app storage can differ. Only after signing in on a device that has the local SprayTrue data will that data upload.

Tests: all existing regression suites plus `tools/test17.js` for password login/signup, duplicate accounts, wrong/unconfirmed/rate-limit errors, no-email login, reset/change password, redirect cleanup, reload/cancel, consent, and password non-persistence. Auth/email requests are mocked: no real recovery email or password change was performed for Brian.

## Multi-device sync (v2.12.0, retained unchanged)

- Backend: **tankmix**, `qcwneqqfiyuouokklnpg`, US West (Oregon), `https://qcwneqqfiyuouokklnpg.supabase.co`. Only its public publishable key is embedded. No database password/service-role credential.
- Existing `public.user_data(user_id,key,value,updated_at,deleted)` table has owner-only SELECT/INSERT/UPDATE/DELETE RLS for `authenticated`; anonymous access is denied. `tankmix_sync(jsonb)` runs as **SECURITY INVOKER** and atomically ignores stale timestamps. Tombstones (`deleted=true`) propagate whole-key deletions without resurrecting old device values.
- Delta response migration: `tools/migrations/20261108_sync_delta_responses.sql`. Sync polling transfers key timestamps only; values are downloaded only when changed. The authenticated atomic sync RPC returns only touched keys, rejects stale writes, and makes the accepted server row win exact timestamp ties.
- Security hardening migration: `tools/migrations/20261108_sync_hardening.sql` revokes public/anon/authenticated EXECUTE on the internal `rls_auto_enable` helper, and unnecessary authenticated TRUNCATE/REFERENCES/TRIGGER privileges. Security advisor: no lints after migration. The older Supabase project was not touched.
- Local `tm.*` JSON keys remain the device's source of truth: library, saved mixes, current draft, logs, fields, settings, calibration, weather stations/API keys, cached weather and EPA data. New writes queue sync (1.5 seconds); open/focus/reconnect and every 30 visible seconds reconcile. Active inputs defer background pulls. Offline edits remain local until a successful retry.
- **First sign-in:** union collections, dedupe products by ID/EPA/WA registration (custom by name), and identical saved mixes irrespective of device-generated IDs. Merge settings/weather accounts without dropping distinct entries. An existing cloud draft takes precedence over a new-device draft. A **device-only pre-sync recovery backup** preserves the complete original device snapshot, including API keys, in case of conflicting data; download it privately from Settings. Ordinary export/import still works unchanged.
- After that, conflict resolution is **whole-key newest `updated_at` wins**, not per-record merging. Simultaneous offline changes to different records within the same library/log key can overwrite one another; keep backups for important jobs. Device clocks must be correct (future timestamps >4 minutes pause sync). Server timestamp checks prevent stale writers from clobbering newer snapshots.
- **Privacy:** `tm.tempest` and `tm.wu` contain personal API tokens. They are intentionally synced to the signed-in user's RLS-protected rows; this is NOT end-to-end encryption. Auth tokens, owner metadata and recovery backups are device-only (`tankmix.*`, never uploaded or included in ordinary backups). Sign-out keeps local data. Switching to another account first archives the former account locally, then starts a separate workspace rather than uploading another user's data.
- **Historical v2.13 compatibility:** older builds share site storage with current versions. Older live builds do not participate in the new per-record merge. Reopen/focus the preview to scan changes made by older builds.

## Share / print PDF (v2.11.0)
- **Share / Save PDF** and **Download PDF** build a real `application/pdf` from the on-screen print sheet (mix or spray-log). Filename ends in `.pdf`.
- Uses a small built-in PDF writer (Helvetica, US Letter) — no html2canvas/jsPDF dependency — so it works offline in the installed PWA and on iOS standalone.
- If the browser can't share files, Share falls back to text share and/or downloading the PDF. **Print** and the on-screen print view are unchanged.

## Tools + Logs tabs (v2.10.0)
- **Lookup** moves under **Tools** with Sprayer and Order. The Tools segmented control is **Sprayer | Order | Lookup**. Crop/site and pest filters stay on Lookup. `showTab("lookup")` and any button that jumped to Lookup open Tools with the Lookup sub-view selected; Tools still remembers the last sub-view.
- **Logs** moves out of Settings into its own bottom tab (where Lookup used to be). Full spray log UI (form, list, filters, CSV, print, saved fields) lives only there — nothing left under Settings. (v2.10.1 removes the leftover Settings › Logs link from the first 2.10.0 preview.)
- Bottom bar is still six tabs: **Mix · Products · Tools · Logs · Weather · Settings**.

## Open saved mixes from Mix (v2.9.x)
- The **Mix** tab has a **Saved Mixes** card at the top with a plain **dropdown** (`<select>`) of `S.mixes` (newest first). Options show name · product count · date. Placeholder: “Choose a saved mix…”. No count badge on the heading (count is in the hint under the dropdown).
- Choosing a mix loads it through the same `openMix` path as Settings › Saved. If the current draft has unsaved changes, a confirm asks before replacing. The select then resets to the placeholder so the same mix can be opened again.
- Empty state: disabled select with “No saved mixes”, plus a hint to tap **Save**. Settings › Saved is unchanged. Clear still works; a toast shows the opened mix name.

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
- Bottom bar (through v2.9): Mix · Products · Tools · Lookup · Weather · Settings. From v2.10: Mix · Products · Tools · Logs · Weather · Settings (Lookup is under Tools). Tools/Products tabs add no new storage keys; Weather Underground adds `tm.wu` (additive). Preview and live keep sharing `tm.*`.


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
- **Key privacy:** keys live in `tm.wu` and are sent to `api.weather.com`; when Account / Sync is enabled they also sync to your private Supabase rows. Left out of backups unless **Include Tempest / Weather Underground API keys** is ticked.
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
- **Token privacy:** tokens are stored in `tm.tempest` on this device and are sent to `swd.weatherflow.com` (as the documented `?token=` parameter, with no cookies or referrer). With Account / Sync enabled, they also sync to your private Supabase rows. They never go into records, CSV, print or share text. **Export backup** includes station names/choices but leaves tokens out unless **Include Tempest access tokens** is ticked. Import adds accounts from a backup that has them (no duplicates).
- **CORS:** `swd.weatherflow.com` answers with `Access-Control-Allow-Origin: *` (also on 401 replies and preflight), so it works from GitHub Pages and from `file://`.
- `better_forecast` is not used (Open-Meteo gives the 80 m temperature for the inversion hint and keeps the outlook the same for both sources).


## Clear mix (v2.4)
The **✕ Clear** button in the Mix tab's "Sprayer & field" heading resets the form to a new blank mix (no products, empty name, default tank/carrier/field size for your units, no fertilizer carrier). It also resets `tm.current`, so a reload stays blank. An **Undo** toast shows for 8 seconds and restores the previous mix exactly. Settings, saved mixes, My products, fields, logs and calibration are not touched. No new storage keys.

Two ways to use it:
- **Single file:** open `index.html` directly (double-click, email it, or copy it to a phone). Everything is inside it.
- **Installable app (PWA):** host the `dist/` folder on any static HTTPS server, open it, and choose "Add to Home Screen" or "Install". It works offline after the first visit. Live EPA search also needs a web address, because EPA blocks pages opened as `file://`.

Published on GitHub Pages (repo briannfink/spraytrue): live root https://briannfink.github.io/spraytrue/ and review copy https://briannfink.github.io/spraytrue/preview/.

## Tabs (bottom bar)
Six tabs: **Mix · Products · Tools · Logs · Weather · Settings**.
- **Mix** — tank mix calculator, Saved Mixes dropdown, products in the mix.
- **Products** — My products + quick EPA/WSDA add.
- **Tools** — Sprayer calibration, mixing Order / jar test, and **Lookup** (EPA + WSDA with crop/site and pest filters).
- **Logs** — spray records, CSV export, print, saved fields.
- **Weather** — Open-Meteo / Tempest / Weather Underground.
- **Settings** — units, theme, weather source, Saved (mixes + backup). Logs are only on the Logs tab.


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
- **Share / Save PDF** shares a real `.pdf` file, with text/download fallbacks when file sharing is unavailable.
- **Download** saves a real `.pdf` file.

iPhone and iPad home-screen apps ignore `window.print()`. The app detects standalone mode (`navigator.standalone` or `display-mode: standalone`) and points to Share instead. If no print dialog opens within 1.5 s on any platform, the same hint appears.

## Updates and preview
- The `dist/sw.js` cache name is `spraytrue-<version>-<build hash>`. Pages load network-first, so a new deploy shows up on the next launch. A new worker activates immediately, and an open page shows "A new version is ready. Tap to refresh".
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
- `src/part13.js`: passwordless Supabase account, offline-first per-key sync and first-contact merge
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

