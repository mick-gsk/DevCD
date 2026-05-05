---
name: image-poster
description: "Installiert aus nexu-io/open-design: erzeugt ein einzelnes Bildmotiv fuer Poster, Key Art oder visuelle Markenexploration. Nuetzlich fuer Logo-Moodboards, Symbolideen, Brand-Atmosphaere und visuelle Richtungen. Verwenden bei poster, key art, illustration, image, cover art, logo concept sheet."
argument-hint: "Beschreibe das Motiv oder die visuelle Richtung, die als einzelnes Marken- oder Logo-Explorationsbild erzeugt werden soll."
---

# Image Poster

Quelle: adaptiert aus nexu-io/open-design, Skill image-poster.

Nutze diese Skill fuer eine einzelne visuelle Richtung oder ein Markenmotiv pro Durchlauf. Fuer Logoarbeit ist sie besonders geeignet, um Symbolstimmung, Formfamilien und Materialitaet zu erkunden, nicht fuer finale Vektorproduktion.

## Workflow

### 0. Projektkontext lesen

Wenn vorhanden, uebernimm aus dem Projekt:

- imageModel
- imageAspect
- imageStyle

Nur nachfragen, wenn diese Werte fehlen oder unklar sind.

### 1. Prompt in dieser Reihenfolge aufbauen

Plane erst, dann generieren.

1. Subject and composition
- Was ist im Bild?
- Welche Form oder welches Emblem steht im Fokus?
- Wie ist Crop, Abstand und Bildaufbau?

2. Lighting and mood
- neutral, studio, moody, warm, cool
- eher praezise oder eher atmosphaerisch

3. Palette and textures
- nutze Markenfarben, falls gegeben
- sonst 2 bis 3 klare Mood-Begriffe

4. Camera or lens
- nur wenn fotorealistische Wirkung explizit gewuenscht ist

5. What to avoid
- kein AI-Slop
- keine kaputten Buchstaben
- keine Platzhalter-Logos
- keine verformten Symbole

### 2. Ein einzelnes Bild erzeugen

Erzeuge genau ein Bild pro Turn, ausser der Nutzer verlangt Varianten.

### 3. Kurz uebergeben

Antworte knapp mit:

- was generiert wurde
- welche Richtung, Palette und Formidee verwendet wurde
- ob das Bild eher fuer Moodboard, Symbolsuche oder Markenatmosphaere gedacht ist

## Harte Regeln

- Genau ein Bild pro Turn, ausser Varianten werden explizit verlangt.
- Seitenverhaeltnis exakt einhalten.
- Keine Textmuell-Platzhalter im Bild.
- Nichts nur beschreiben, wenn stattdessen ein echtes Motiv erzeugt werden kann.
- Fuer finale Logos immer darauf hinweisen: dieses Ergebnis ist Konzeptmaterial, keine fertige Vektor-Marke.