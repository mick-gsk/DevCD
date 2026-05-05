---
name: design-brief
description: "Installiert aus nexu-io/open-design: strukturiert ein vages Marken- oder Logo-Briefing in eine konkrete Design-Spezifikation mit Palette, Typografie, Stimmung, Dichte und Constraints. Verwenden bei design brief, logo brief, brand brief, structured brief, ilang brief."
argument-hint: "Beschreibe das Marken- oder Logo-Briefing, das in eine konkrete Designspezifikation aufgeloest werden soll."
---

# Design Brief

Quelle: adaptiert aus nexu-io/open-design, Skill design-brief.

Nutze diese Skill, wenn ein unscharfes Briefing zuerst in klare Designentscheidungen uebersetzt werden muss, bevor Logos oder Markenassets entworfen werden.

## Ziel

Ueberfuehre ein strukturiertes oder freies Briefing in eine konkrete Design-Spezifikation. Eliminiere schwammige Begriffe wie clean, premium oder editorial, indem du sie in explizite Dimensionen aufloest.

## Workflow

### 1. Eingang verstehen

Akzeptiere entweder:

- ein strukturiertes Briefing im Stil von I-Lang
- oder natürliches Briefing in Alltagssprache

Wenn der Input frei formuliert ist, mappe ihn zuerst auf diese Dimensionen:

- Palette
- Akzentfarbe
- Body-Typografie
- Display-Typografie
- Layout-Modell
- Stimmung
- Dichte
- Ausschluesse oder Constraints

### 2. Dimensionen validieren

Arbeite mit einer geschlossenen Auswahl, statt Werte frei zu erfinden.

Beispielwerte:

- Palette: navy_and_white, monochrome_dark, light_clean, earth_tones
- Accent: coral, electric_blue, emerald, muted_sage, slate
- Typography: inter, system_ui, dm_sans, georgia
- Display: space_grotesk, clash_display, same_as_body, playfair
- Layout: single_column, two_column, asymmetric
- Mood: professional_minimal, playful, brutalist, editorial
- Density: compact, balanced, spacious
- Exclude: animations, gradients, stock_photos, carousel

Wenn ein Wert unklar oder ungueltig ist, frage gezielt nach, statt zu raten.

### 3. Defaults transparent aufloesen

Wenn Dimensionen fehlen, waehle sichere Defaults und dokumentiere sie explizit.

Beispielregeln:

- editorial -> light_clean plus playfair
- brutalist -> monochrome_dark plus space_grotesk
- sonst -> light_clean plus same_as_body
- density default -> balanced
- exclude default -> none

### 4. Spezifikation erzeugen

Erstelle eine konkrete Design-Spezifikation mit mindestens diesen Bereichen:

- Visual Theme and Atmosphere
- Color Palette and Roles
- Typography Rules
- Component Stylings
- Layout Principles
- Depth and Elevation
- Dos and Donts
- Responsive Behavior
- Agent Prompt Guide

Alle Farben, Schriftstapel und Spacing-Werte muessen aus den aufgeloesten Tokens stammen. Keine freien zusaetzlichen Tokens erfinden.

### 5. Optional eine kurze Vorschau beschreiben

Falls der Nutzer eine Preview will, liefere eine knappe Dokumentationsansicht mit:

- Farbflaechen und Hex-Werten
- Typo-Proben
- Spacing-Ruler
- 2 bis 3 Beispielkomponenten

### 6. Aufloesungen dokumentieren

Schliesse mit einer kurzen Liste der automatisch gesetzten Defaults ab, inklusive Regel, warum sie gewaehlt wurden.

## Harte Regeln

- Keine stillen Annahmen.
- Keine erfundenen Hex-Werte ausserhalb der aufgeloesten Palette.
- Keine zusaetzlichen Fonts ausser Body, Display und optional Mono.
- Unbekannte Werte immer klaeren.
- Die Spezifikation soll fuer nachgelagerte Logo- oder Brand-Arbeit direkt verwendbar sein.