# @errunorsk – automatisk drift

Dette repoet driver Instagram-kontoen **@errunorsk**: quizinnlegg om norske dialektord («Gjett ordet»).
Eier: Jørgen. Han vil ikke godkjenne innlegg selv. Claude publiserer direkte, men gjør en grundig
egenkontroll før hvert innlegg planlegges.

## Faste verdier
- Metricool-merkevare (blogId): `7570130`, kun Instagram (`errunorsk`). Bruk tidssone `Europe/Madrid` i Metricool (samme tid som Oslo).
- **Format: Reels** (fra 26.11.2026). Videoer og forsidebilder ligger i `reels/` og hentes av Metricool via
  `https://raw.githubusercontent.com/jorgensolgaard-code/errunorsk-bilder/main/reels/<id>.mp4` og `.../reels/<id>-cover.png`
  (filene må være pushet før innlegget planlegges). `bilder/` inneholder de gamle enkeltbildene og brukes ikke lenger.
- Svaret skal ALDRI stå i bildeteksten. Svaret avsløres i slutten av videoen, slik at folk gjetter i kommentarfeltet.
- Alle brukte ord står i `data/ord.json`. Et ord som står der, skal ALDRI brukes igjen.

## Regler for planleggingen
- Hold alltid **10–14 dager** med planlagte innlegg foran dagens dato.
- Metricool er gratisversjonen: **maks 20 publiserte innlegg per kalendermåned**. Tell innlegg som allerede er planlagt i hver måned, og gå aldri over 20.
- Ett innlegg om gangen, kl. 12:00, omtrent annenhver dag (mønster: 2 dager, 1 dag, 2 dager … så 20 fyller en måned).
- Landsdelene går på rundgang (Nord-Norge, Trøndelag, Vestlandet, Østlandet, Sørlandet). Aldri to fra samme landsdel etter hverandre.
- Riktig svar fordeles jevnt på A, B og C.
- Varier innen Vestlandet og Østlandet (ikke bare Bergen og Oslo: Stavanger, Sunnmøre, Hardanger, Hedmark, Gudbrandsdalen, Telemark, Valdres osv.).

## Fremgangsmåte for én kjøring
1. Hent planlagte innlegg med Metricool `getScheduledPosts` (blogId 7570130) for de neste ~45 dagene. Finn siste planlagte dato og antall per måned.
2. Hvis siste planlagte dato er mindre enn 10 dager frem: legg til innlegg til siste dato er 12–14 dager frem, innenfor månedsgrensen. Ellers: gjør ingenting og avslutt.
3. Finn nye ord. KRAV til hvert ord:
   - Betydningen må bekreftes i minst én pålitelig kilde du faktisk har åpnet (SNL, Lokalhistoriewiki, Norsk Ordbok/Nynorskordboka/ordbokene.no, kommunale eller universitetssider, Wiktionary). Lagre kilden i `kilde`.
   - Ordet skal være tydelig dialektalt (ikke vanlig bokmål/nynorsk med samme betydning).
4. Lag to feilsvar per ord. Egenkontroll: et feilsvar må IKKE være en gyldig betydning av ordet på bokmål, nynorsk eller i en annen dialekt (eks.: «dokker» kan bety båthavner på bokmål, så det kan ikke være feilsvar). Feilsvarene skal være troverdige, ikke tullete.
5. Skriv eksempelsetning i dialektens former (bruk kildenes bøyning, f.eks. bergensk fortid -æt, sørlandsk «kåmme»).
6. Legg ordene til i `data/ord.json` (samme felt som eksisterende: id, date, ord, landsdel, valg, riktig, betyr, eksempel, dialekt, tag, kilde, status). id = løpenummer med tre siffer + ord uten æøå (æ→ae, ø→o, å→a).
7. Lag videoene: `python3 verktoy/render_reel.py <json med de nye ordene> reels/`. Lager `<id>.mp4` (1080x1920, 9,5 s: spørsmål → nedtelling 3-2-1 → riktig svar markeres + eksempelsetning) og `<id>-cover.png`. Tar ca. 15 s per ord; kjør maks 4 ord per kommando (eller to kommandoer parallelt) for å unngå tidsavbrudd. Krever Playwright, Chromium og ffmpeg (finnes i miljøet).
8. **Kontroller hver video** før opplasting: trekk ut et bilde fra slutten (`ffmpeg -ss 9 -i reels/<id>.mp4 -frames:v 1 ut.png`) og les det, og les `<id>-cover.png`. Sjekk at RIKTIG alternativ er markert (sammenlign med `riktig` i ord.json), at ordet ikke går ut over kanten, ingen skrivefeil og riktig landsdel.
9. Commit og push `reels/` og `data/ord.json` til `main`.
10. Planlegg hvert innlegg med Metricool `createScheduledPost`: `media: [<mp4-url>]`, `videoThumbnailUrl: <cover-url>`, `draft: false`, `autoPublish: true`, `instagramData: {"type": "REEL", "showReelOnFeed": true, "isAiGenerated": false}`, alt-tekst `Quiz: Hva betyr <ord>? A …, B …, C …`.

## Bildetekst (mal)
```
Hva betyr «<ord>»? Skriv A, B eller C i kommentarfeltet før svaret dukker opp i videoen!

Hva sier dere der du bor? 👇

#dialekt #dialektord <#landsdelstag> #norsk #errunorsk
```
Ikke ta med svar, betydning eller eksempelsetning i bildeteksten.

## Rapport
Avslutt med en kort melding på norsk til Jørgen: hvor mange innlegg som ble lagt til, hvilke datoer, og om noe gikk galt.
Hvis noe feiler (Metricool, GitHub-push, mangel på kilder): ikke planlegg halvferdige innlegg; si fra hva som stoppet.
