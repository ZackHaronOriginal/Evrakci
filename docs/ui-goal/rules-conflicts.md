# Rules that differ from, or wait on, the owner

Where an Apple HIG rule and our decisions disagree, ours applies now (Fluent 2 direction A and
D1-D13 win over HIG, owner rule 2026-11-19). The tool reports against ours. Rule ids are in
`docs/ui-goal/rules.json`; nothing here is enforced until the owner says so.

## Differs (13): ours applies, please confirm

| Rule | Ours | Applies now | Question for the owner |
|---|---|---|---|
| HIG-SPC-04 icon-to-edge padding about 10 px | Icon 16/20 in a 36 px button = 8-10 px inset (A deviation 5) | Ours | Keep the 8-10 px inset? yes / no |
| HIG-FOC-03 ring for fields, full-row highlight for lists | D11 ring on every focusable widget; list rows get a selection fill plus the ring | Ours (item views draw the ring per item, tool reports them "skip") | Keep fill plus ring on list rows? yes / no |
| HIG-FOC-07 respect standard shortcuts | Ctrl instead of Cmd; the I key is unreliable on Turkish keyboards | Ours | Keep Windows-style shortcuts and no I key? yes / no |
| HIG-TYP-01 default 13 pt, minimum 10 pt | Body 15 px, caption 13 px is the floor (D4) | Ours (rule DEC-TYP-01) | Keep 13 px as the floor? yes / no |
| HIG-TYP-02 Apple's text style ramp | 13/15/17/20/24 px steps (D4) | Ours (rule DEC-TYP-02) | Keep our five steps? yes / no |
| HIG-CON-01 4.5:1 text, 3:1 large or bold | Body and table 7:1, secondary 4.5:1, edges and icons 3:1 (D10) | Ours (rules DEC-CON-01..03) | Keep 7:1 for body text? yes / no |
| HIG-CON-05 no app-specific light/dark setting | Follows the OS by default, manual override in Ayarlar (D9) | Ours | Keep the override? yes / no |
| HIG-WIN-01 no custom window frame | Custom Mica title band with tabs (direction A) | Ours, with Windows min/max/close and snap kept | Keep the custom band? yes / no |
| HIG-WIN-04 no critical action in a bottom bar | Status bar holds only the zoom slider; the main action is in the command bar | Ours | Confirm the status bar stays non-critical? yes / no |
| HIG-WIN-05 window title about 15 characters, not the app name | Job name, any length, elided with a tooltip | Ours | Keep long job names in the title? yes / no |
| HIG-WIN-08 menu labels: verb phrase, title case | Turkish sentence case, "Kontrol" vocabulary | Ours | Keep sentence case? yes / no |
| HIG-WIN-13 menu bar shows the same items always | No resting menu row; menus open on Alt (A deviation 1); items disabled, not hidden | Ours | Keep menus on Alt only? yes / no |
| HIG-WIN-15 alert buttons, default on the trailing side | Fluent button order for the default button; at most three buttons, no bare "OK" kept | Fluent order | Keep Fluent order, max 3 buttons? yes / no |

## Owner (7): the decision is open

| Rule | Ours | Applies now | Question for the owner |
|---|---|---|---|
| HIG-SPC-03 about 12 pt around bezelled controls, 24 pt around borderless ones | D6 scale {4,8,12,16,24,32,48}; 4-8 px between toolbar buttons | Ours (4-8 px) | Keep 8 px between 36 px icon buttons (A), or widen to 12 px? |
| HIG-CTL-07 activity indicator inside a button for slow actions | D7 allows progress above 240 ms; not placed yet | Status-bar progress only | Spinner inside the button, or status-bar progress only? |
| HIG-FOC-04 selected list row: accent fill when focused, gray when not | Accent #3f5a4c; inactive selection colour not decided | Selection fill as built | Inactive selection: gray (HIG) or a 20 % accent tint? |
| HIG-MOT-06 avoid auto-dismissing UI | Toast timing not decided | As built | Toasts stay until dismissed, or 6 s or more with hover-pause and a log entry? |
| HIG-ICO-06 app icon sizes 16/32/128/256/512 | Windows .ico 16-256 | As built | Ship 16/24/32/48/256 in the .ico? (The macOS list does not apply.) |
| HIG-WIN-03 active and inactive windows look different | Not specified in A | Unchanged | Dim the title band when the window is inactive (as Fluent does), or leave it? |
| HIG-WIN-14 standard menu order and shortcuts | Our own menus: Alt+D/E/G/T/A/Y (Turkish) | Ours | Keep our order, or map to Dosya/Düzen/Görünüm/Pencere/Yardım? |
