# Proposals for the owner (not applied)

Direction A is the visual source of truth (decisions.md, "Owner correction after round 3").
Nothing below has been applied to the mockups, except item 3, whose option a is what the
provisional 150 % renders show today (it was there before this list and needs the owner's choice).
Each item changes or extends how A behaves and waits for the owner's yes or no.

1. **Edge above the pinned inspector action at 150 % text.** At 150 % the inspector content
   scrolls (as a QScrollArea) and used to run straight under the pinned primary ("Belgeyi onayla",
   "Onayla ve sonrakine geç"), so a half-visible line sat directly on the button
   (`png/kontrol-150-light.png`, `png/degerler-150-light.png`). The buttons now sit below the
   scroll area instead of over it (see REVIEW.md), but a cut line can still end right above them.
   Proposal: when the pane is scrolled, show A's 1 px `--stroke` hairline above the pinned
   button group. At 100 % nothing would change, since nothing scrolls there.
2. **Değerler table at 150 % text.** At 150 % the table scrolls sideways and the Güven column
   goes out of view first. Proposal: pin the Güven column at the right edge, or move it next to
   the edited value, so the Kontrol word stays visible. A's 100 % layout would stay as it is.
3. **Title-band tabs at 150 % text (decision needed; the 150 % renders are provisional until then).**
   At 150 % on a 1366 px window, A's six labelled tabs, the job name with "Kaydedildi", the search,
   ≡ and the caption buttons no longer fit in one 44 px band. The 150 % renders currently show
   every unselected tab as its icon only (name in the tooltip), the selected tab keeps its icon and
   label (`additions.css`, "150 % text" block; `png/*-150-light.png`). That changes how A's
   approved tabs look at that size, so it needs the owner's choice:
   - **a. Icon-only unselected tabs** (as rendered now). Everything stays in the band; the tab
     names are only in tooltips, so a new user has to hover to learn them.
   - **b. Keep the labels, overflow behind a chevron.** Tabs keep A's icon + label; the tabs that
     do not fit go into a "»" menu at the end of the strip (Fluent TabView overflow). The order and
     the Ctrl+1–6 keys stay; the hidden tabs are one click away.
   - **c. Shrink the job name first.** Tabs keep A's icon + label; the job name is elided with
     "…" (full name in the tooltip and in the job-switch menu), and "Kaydedildi 14:32" shows only
     its check icon. Only if that is still not enough does b or a apply.
   A's 100 % layout is the same under all three.
   *Phase 2 review note (115 % and 130 %, which A does not draw):* on Windows at 1366 px with the
   caption buttons, A's six labelled tabs fit at 100 % and 115 % but not at 130 % (the band needs
   about 1466 px). So that nothing overlaps, the Qt band applies the same provisional tab rule
   (option a) below 150 % only while the labelled tabs do not fit, and the job name elides with
   "…" (full name in its tooltip and accessible name). Both live in `theme.title_band_rule`
   (`fits` argument) and `TitleBand.fit`; whichever option the owner picks replaces that branch.
4. **"Kontrol'e geç" twice on Yükle.** It is both the command-bar button and the inspector's
   primary, with the same icon, close together (`png/yukle-light.png`). A does the same with
   "Değerlerde aç" (menu + inspector), so it follows A's pattern and is left as it is. Option: once
   the inspector primary exists, drop the command-bar copy (it stays in the Git menu and Ctrl+2).
5. **Scroll areas at 150 % text show a cut row at the edge.** At 150 % the inspector content and
   the Kontrol timeline scroll (they do not fit), so the last visible row is cut by the scroll
   area's edge (e.g. "Filtre uygula" above "Belgeyi onayla" in `png/kontrol-150-light.png`). The
   pinned buttons now sit below the scroll area instead of over it, and the thin scrollbar shows
   there is more. Together with item 1 (hairline above the pinned buttons) the owner could also
   choose to let the inspector scroll per card (a cut card is never shown; the gap is left empty).

Apart from item 3 (which describes a change already visible in the provisional 150 % renders
and asks for a decision), no proposal touches the title band, logo, tabs, ≡, job name, search, caption buttons, command
bar, overview strip, inspector cards, buttons, spacing, radii, colours, fonts, labels or icons.
