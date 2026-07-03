# -*- coding: utf-8 -*-
"""German/English lemma and transfer-word helpers."""

from __future__ import annotations

import re


def normalize_lookup(text: str) -> str:
    """Normalize lookup keys while preserving Goa'uld glottal stops."""
    normalized = str(text).strip().lower()
    normalized = normalized.replace("’", "'").replace("´", "'").replace("`", "'")
    normalized = re.sub(r"\s+", " ", normalized)
    return normalized


# ─────────────────────────────────────────────────────────────────────────────
# FUNCTION WORDS / TRANSFER CLASSES
# ─────────────────────────────────────────────────────────────────────────────

# Only true transfer/function words are skipped. Semantic markers such as
# negation (nicht/kein/not/no), modals (muss/kann/must/can), yes/no and
# conjunctions stay translatable through YAML/overlay maps.
GERMAN_ARTICLES: frozenset[str] = frozenset({
    "der", "die", "das", "dem", "den", "des",
    "ein", "eine", "einen", "einem", "einer", "eines",
})
GERMAN_PREPOSITIONS: frozenset[str] = frozenset({
    "in", "im", "an", "am", "auf", "bei", "mit", "nach", "seit", "von",
    "vor", "zu", "zum", "zur", "durch", "für", "gegen", "ohne", "um",
    "über", "unter", "zwischen", "aus", "bis", "hinter", "neben",
})
GERMAN_AUXILIARIES: frozenset[str] = frozenset({
    "bin", "bist", "ist", "sind", "seid", "sein", "sei", "war", "waren",
    "wart", "gewesen", "habe", "hast", "hat", "haben", "habt", "hatte",
    "hatten", "werde", "wirst", "wird", "werden", "werdet", "würde",
    "würden",
})
GERMAN_MODAL_SEMANTIC: frozenset[str] = frozenset({
    "kann", "kannst", "können", "könnt", "muss", "musst", "müssen",
    "soll", "sollen", "sollst",
})
GERMAN_LIGHT_PARTICLES: frozenset[str] = frozenset({
    "auch", "nur", "schon", "noch", "doch", "sondern", "denn", "als",
    "sehr", "gar", "mal", "nun", "so",
})
GERMAN_STOP_WORDS: frozenset[str] = (
    GERMAN_ARTICLES | GERMAN_PREPOSITIONS | GERMAN_AUXILIARIES | GERMAN_LIGHT_PARTICLES
)

ENGLISH_ARTICLES: frozenset[str] = frozenset({"a", "an", "the"})
ENGLISH_PREPOSITIONS: frozenset[str] = frozenset({
    "in", "on", "at", "by", "with", "from", "for", "to", "of", "into",
    "onto", "over", "under", "between", "through", "before", "after",
    "within", "without", "as",
})
ENGLISH_AUXILIARIES: frozenset[str] = frozenset({
    "am", "are", "is", "be", "being", "been", "was", "were", "do", "does",
    "did", "have", "has", "had", "will", "would",
})
ENGLISH_MODAL_SEMANTIC: frozenset[str] = frozenset({
    "shall", "should", "can", "could", "may", "might", "must",
})
ENGLISH_LIGHT_PARTICLES: frozenset[str] = frozenset({"just", "very", "already", "still"})
ENGLISH_STOP_WORDS: frozenset[str] = (
    ENGLISH_ARTICLES | ENGLISH_PREPOSITIONS | ENGLISH_AUXILIARIES | ENGLISH_LIGHT_PARTICLES
)

STOP_WORDS_BY_LANG: dict[str, frozenset[str]] = {
    "de": GERMAN_STOP_WORDS,
    "en": ENGLISH_STOP_WORDS,
}


# ─────────────────────────────────────────────────────────────────────────────
# GERMAN LEMMATIZER
# ─────────────────────────────────────────────────────────────────────────────

# Trennbare/untrennbare Verbpräfixe (längste zuerst geprüft)
_DE_PREFIXES: tuple[str, ...] = (
    "zurück", "wieder", "gegen", "unter", "über", "durch", "ent", "emp",
    "miss", "nach", "fort", "voll", "weg", "her", "hin", "los", "mit",
    "vor", "auf", "aus", "ein", "ab", "an", "be", "er", "ge", "um",
    "ver", "zer", "zu",
)

# Unregelmäßige Vollformen → Lemma (3sg mit Ablaut/Umlaut, Präteritum, Partizip II,
# Imperativstämme). Präfixverben werden über _DE_PREFIXES + Reststamm abgedeckt.
_DE_IRREGULAR: dict[str, str] = {
    # 3. Person Singular (Ablaut/Umlaut)
    "gibt": "geben", "nimmt": "nehmen", "sieht": "sehen", "liest": "lesen",
    "isst": "essen", "frisst": "fressen", "stirbt": "sterben", "wirft": "werfen",
    "hilft": "helfen", "bricht": "brechen", "spricht": "sprechen",
    "sticht": "stechen", "trifft": "treffen", "tritt": "treten",
    "hält": "halten", "fällt": "fallen", "fängt": "fangen", "lässt": "lassen",
    "läuft": "laufen", "schläft": "schlafen", "trägt": "tragen",
    "schlägt": "schlagen", "wächst": "wachsen", "gräbt": "graben",
    "fährt": "fahren", "stößt": "stoßen", "wäscht": "waschen",
    "gilt": "gelten", "misst": "messen", "rät": "raten", "bläst": "blasen",
    "befiehlt": "befehlen", "vergisst": "vergessen", "weiß": "wissen",
    # Imperativ-/Kurzstämme
    "gib": "geben", "nimm": "nehmen", "sieh": "sehen", "lies": "lesen",
    "iss": "essen", "stirb": "sterben", "wirf": "werfen", "hilf": "helfen",
    "brich": "brechen", "sprich": "sprechen", "triff": "treffen",
    # Präteritum
    "gab": "geben", "nahm": "nehmen", "sah": "sehen", "las": "lesen",
    "aß": "essen", "fraß": "fressen", "starb": "sterben", "warf": "werfen",
    "half": "helfen", "brach": "brechen", "sprach": "sprechen",
    "stach": "stechen", "traf": "treffen", "trat": "treten",
    "hielt": "halten", "fiel": "fallen", "fing": "fangen", "ließ": "lassen",
    "lief": "laufen", "schlief": "schlafen", "trug": "tragen",
    "schlug": "schlagen", "wuchs": "wachsen", "grub": "graben",
    "fuhr": "fahren", "stieß": "stoßen", "wusch": "waschen",
    "galt": "gelten", "maß": "messen", "riet": "raten",
    "fand": "finden", "band": "binden", "sang": "singen",
    "sprang": "springen", "trank": "trinken", "sank": "sinken",
    "zwang": "zwingen", "schwamm": "schwimmen", "gewann": "gewinnen",
    "begann": "beginnen", "kam": "kommen", "ging": "gehen",
    "stand": "stehen", "saß": "sitzen", "lag": "liegen", "tat": "tun",
    "zog": "ziehen", "flog": "fliegen", "floh": "fliehen", "log": "lügen",
    "bog": "biegen", "bot": "bieten", "fror": "frieren", "schwor": "schwören",
    "stahl": "stehlen", "blieb": "bleiben", "schrieb": "schreiben",
    "schrie": "schreien", "stieg": "steigen", "schwieg": "schweigen",
    "griff": "greifen", "litt": "leiden", "stritt": "streiten",
    "schnitt": "schneiden", "riss": "reißen", "schoss": "schießen",
    "schloss": "schließen", "floss": "fließen", "flossen": "fließen",
    "dachte": "denken", "brachte": "bringen", "wusste": "wissen",
    "kannte": "kennen", "nannte": "nennen", "brannte": "brennen",
    "sandte": "senden", "wandte": "wenden", "rannte": "rennen",
    "gebar": "gebären", "starben": "sterben", "gaben": "geben",
    "nahmen": "nehmen", "sahen": "sehen", "kamen": "kommen",
    "gingen": "gehen", "standen": "stehen", "fanden": "finden",
    "hielten": "halten", "ließen": "lassen", "zogen": "ziehen",
    # Partizip II (Vollformen)
    "gefunden": "finden", "gebunden": "binden", "gesungen": "singen",
    "gesprungen": "springen", "getrunken": "trinken", "gesunken": "sinken",
    "gezwungen": "zwingen", "geschwommen": "schwimmen", "gewonnen": "gewinnen",
    "begonnen": "beginnen", "gekommen": "kommen", "gegangen": "gehen",
    "gestanden": "stehen", "gesessen": "sitzen", "gelegen": "liegen",
    "getan": "tun", "gezogen": "ziehen", "geflogen": "fliegen",
    "geflohen": "fliehen", "gelogen": "lügen", "gebogen": "biegen",
    "geboten": "bieten", "gefroren": "frieren", "geschworen": "schwören",
    "gestohlen": "stehlen", "geblieben": "bleiben", "geschrieben": "schreiben",
    "geschrien": "schreien", "gestiegen": "steigen", "geschwiegen": "schweigen",
    "gegriffen": "greifen", "gelitten": "leiden", "gestritten": "streiten",
    "geschnitten": "schneiden", "gerissen": "reißen", "geschossen": "schießen",
    "geschlossen": "schließen", "geflossen": "fließen", "gegeben": "geben",
    "genommen": "nehmen", "gesehen": "sehen", "gelesen": "lesen",
    "gegessen": "essen", "gefressen": "fressen", "gestorben": "sterben",
    "geworfen": "werfen", "geholfen": "helfen", "gebrochen": "brechen",
    "gesprochen": "sprechen", "gestochen": "stechen", "getroffen": "treffen",
    "getreten": "treten", "gehalten": "halten", "gefallen": "fallen",
    "gefangen": "fangen", "gelaufen": "laufen", "geschlafen": "schlafen",
    "getragen": "tragen", "geschlagen": "schlagen", "gewachsen": "wachsen",
    "gegraben": "graben", "gefahren": "fahren", "gestoßen": "stoßen",
    "gewaschen": "waschen", "gegolten": "gelten", "gemessen": "messen",
    "geraten": "raten", "gedacht": "denken", "gebracht": "bringen",
    "gewusst": "wissen", "gekannt": "kennen", "genannt": "nennen",
    "gebrannt": "brennen", "gesandt": "senden", "gewandt": "wenden",
    "gerannt": "rennen", "geboren": "gebären", "gestorben ": "sterben",
    # Reststämme nach Präfix-Abtrennung (z. B. verloren → ver+loren)
    "loren": "lieren", "lor": "lieren", "liert": "lieren",
    "nommen": "nehmen", "geben": "geben", "standen": "stehen",
    "gangen": "gehen", "schworen": "schwören", "brochen": "brechen",
    "sprochen": "sprechen", "troffen": "treffen", "griffen": "greifen",
    "zogen ": "ziehen", "rät ": "raten",
}


def _de_suffix_candidates(form: str) -> list[str]:
    """Regelbasierte Grundform-Kandidaten für EINE Oberflächenform."""
    out: list[str] = []
    n = len(form)
    add = out.append

    # ── Verben: Präsens/Imperativ ──
    if form.endswith("est") and n > 5:
        stem = form[:-3]
        add(stem + "en"); add(stem + "n"); add(stem)
    if form.endswith("st") and n > 4:
        stem = form[:-2]
        add(stem + "en"); add(stem + "n"); add(stem); add(stem + "e")
    if form.endswith("et") and n > 4:
        stem = form[:-2]
        add(stem + "en"); add(stem)                      # findet→finden, wartet→warten
    if form.endswith("t") and n > 3:
        stem = form[:-1]
        add(stem + "en"); add(stem + "n"); add(stem)     # opfert→opfern, lauert→lauern
    if form.endswith("e") and n > 3:
        stem = form[:-1]
        add(stem + "en"); add(stem + "n"); add(stem)     # opfere→opfern, schwöre→schwören
    if form.endswith("en") and n > 4:
        add(form[:-2]); add(form[:-1])                   # Nomen-Plural / eln→el
    if form.endswith("n") and n > 4 and not form.endswith("en"):
        add(form[:-1])

    # ── Verben: Präteritum schwach ──
    for suf, cut in (("etest", 5), ("etet", 4), ("eten", 4), ("ete", 3),
                     ("test", 4), ("tet", 3), ("ten", 3), ("te", 2)):
        if form.endswith(suf) and n > cut + 2:
            stem = form[:-cut]
            add(stem + "en"); add(stem + "n")            # wartete→warten, opferte→opfern

    # ── Partizip II regelmäßig: ge…t / ge…et ──
    if form.startswith("ge") and n > 5:
        rest = form[2:]
        add(rest)
        out.extend(_de_suffix_candidates(rest))          # gemacht→macht→machen

    # ── Nomen/Adjektive: Flexion, Plural, Steigerung ──
    for suf in ("innen", "sten", "stem", "ster", "stes", "ste",
                "ern", "nen", "es", "er", "em", "en", "e", "s", "n"):
        if form.endswith(suf) and n > len(suf) + 2:
            add(form[:-len(suf)])
    if form.endswith("innen") and n > 7:
        add(form[:-3])                                   # königinnen→königin

    # ── Imperativ-/Stammform ohne Endung → Infinitiv raten ──
    if not form.endswith(("e", "n", "t", "s")) and n > 2:
        add(form + "en"); add(form + "n")                # kämpf→kämpfen

    # ── Ableitungssuffixe ──
    for suf in ("heit", "keit", "ung", "bar", "sam", "lich", "isch",
                "haft", "los", "voll"):
        if form.endswith(suf) and n > len(suf) + 2:
            add(form[:-len(suf)])
    if form.endswith("ung") and n > 5:
        add(form[:-3] + "en")                            # eroberung→erobern? (-ung→-en)
        add(form[:-3] + "n")

    return out


def _de_irregular_lookup(form: str) -> list[str]:
    out: list[str] = []
    hit = _DE_IRREGULAR.get(form)
    if hit:
        out.append(hit)
    # du-Form eines unregelmäßigen Verbs: gibst → gibt → geben
    if form.endswith("st") and len(form) > 4:
        hit = _DE_IRREGULAR.get(form[:-2] + "t") or _DE_IRREGULAR.get(form[:-2])
        if hit:
            out.append(hit)
    # ihr-Form: gebt → geben (regulär), aber haltet→halten via Suffixregeln
    return out


_DE_UMLAUT_PLAIN = str.maketrans("äöü", "aou")
_DE_DIGRAPH = (("ä", "ae"), ("ö", "oe"), ("ü", "ue"), ("ß", "ss"))


def de_lemma_candidates(word: str) -> list[str]:
    """
    Return possible German base forms for a word.

    Deckt ab: regelmäßige Konjugation (Präsens, Präteritum, Partizip II,
    Imperativ, -eln/-ern-Verben), ~150 starke Verbformen, Präfixverben,
    Nomen-/Adjektivflexion, Umlaut-Rückbildung sowie ae/oe/ue-Digraph-
    Varianten für Alt-Glossen im Lexikon.
    """
    w = normalize_lookup(word)
    candidates: list[str] = [w]

    # 1) Unregelmäßige Vollformen
    candidates += _de_irregular_lookup(w)

    # 2) Regelbasierte Kandidaten auf der Originalform
    candidates += _de_suffix_candidates(w)

    # 3) Präfixverben: Präfix abtrennen, Rest analysieren, Präfix wieder ansetzen
    for pre in _DE_PREFIXES:
        if w.startswith(pre) and len(w) - len(pre) >= 3:
            rest = w[len(pre):]
            sub = _de_irregular_lookup(rest) + _de_suffix_candidates(rest)
            candidates += [pre + c for c in sub]
            # Partizip mit Binnen-ge: aufgebaut → auf + gebaut → aufbauen
            if rest.startswith("ge") and len(rest) > 5:
                inner = rest[2:]
                sub2 = _de_irregular_lookup(inner) + _de_suffix_candidates(inner)
                candidates += [pre + c for c in sub2]
            break

    # 3b) Zweiter Pass: erzeugte Kandidaten durch die Irregular-Tabelle
    #     (flohen → floh → fliehen, gaben → gab → geben)
    for c in list(candidates):
        hit = _DE_IRREGULAR.get(c)
        if hit:
            candidates.append(hit)

    # 4) Umlaut-Rückbildung (trägt → tragt → tragen)
    plain = w.translate(_DE_UMLAUT_PLAIN).replace("ß", "ss")
    if plain != w:
        candidates.append(plain)
        candidates += _de_suffix_candidates(plain)

    # 5) Kontraktionen
    kontraktionen: dict[str, str] = {
        "im": "in dem", "zum": "zu dem", "ans": "an das",
        "ams": "an dem", "ins": "in das", "beim": "bei dem", "vom": "von dem",
    }
    if w in kontraktionen:
        candidates.extend(kontraktionen[w].split())

    # 6) Digraph-Varianten für Alt-Glossen (schwören → schwoeren)
    with_digraphs: list[str] = []
    for c in candidates:
        v = c
        for uml, dig in _DE_DIGRAPH:
            v = v.replace(uml, dig)
        if v != c:
            with_digraphs.append(v)
    candidates += with_digraphs

    seen: set[str] = set()
    result: list[str] = []
    for c in candidates:
        if c and c not in seen:
            seen.add(c)
            result.append(c)
    return result


def en_lemma_candidates(word: str) -> list[str]:
    """Small English lemmatizer for low-resource direct lookup."""
    w = normalize_lookup(word)
    candidates = [w]

    irregular: dict[str, list[str]] = {
        "am": ["be"], "are": ["be"], "is": ["be"], "was": ["be"], "were": ["be"],
        "i'm": ["i"], "you're": ["you"], "we're": ["we"], "they're": ["they"],
        "don't": ["do not", "not"], "dont": ["do not", "not"],
        "doesn't": ["does not", "not"], "doesnt": ["does not", "not"],
        "didn't": ["did not", "not"], "didnt": ["did not", "not"],
    }
    candidates.extend(irregular.get(w, []))

    if w.endswith("ies") and len(w) > 4:
        candidates.append(w[:-3] + "y")
    if w.endswith("es") and len(w) > 3:
        candidates.append(w[:-2])
    if w.endswith("s") and len(w) > 3 and not w.endswith("ss"):
        candidates.append(w[:-1])
    if w.endswith("ing") and len(w) > 5:
        stem = w[:-3]
        candidates.extend([stem, stem + "e"])
    if w.endswith("ed") and len(w) > 4:
        stem = w[:-2]
        candidates.extend([stem, stem + "e"])

    seen: set[str] = set()
    result: list[str] = []
    for candidate in candidates:
        if candidate and candidate not in seen:
            seen.add(candidate)
            result.append(candidate)
    return result
