# -*- coding: utf-8 -*-
"""
Mathematik 1 — Interaktive Lernplattform (Klausurvorbereitung, Ziel: 1,0)
THI Wirtschaftsingenieurwesen · Streamlit App

Start:  streamlit run app.py
"""

import json
import math
import random
import time
from datetime import datetime

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import streamlit as st

# ----------------------------------------------------------------------------
# Seitenkonfiguration & CSS
# ----------------------------------------------------------------------------

st.set_page_config(
    page_title="Mathe 1 · Klausur-Coach",
    page_icon="📐",
    layout="wide",
    initial_sidebar_state="expanded",
)

DARK_CSS = """
<style>
:root {
  --box-bg: #1B222C; --box-border: #2E3947; --accent: #FFD166;
  --teal: #4FD1C5; --warn: #F6AD55; --err: #FC8181; --ok: #68D391;
  --muted: #9AA5B1;
}
.block-container { padding-top: 2.2rem; }
h1, h2, h3 { letter-spacing: -0.01em; }
div[class*="st-key-box-"] {
  background: var(--box-bg); border-radius: 8px;
  padding: 0.9rem 1.1rem; margin: 0.6rem 0;
}
div[class*="st-key-box-mk"] { border-left: 4px solid var(--teal); }
div[class*="st-key-box-wb"] { border-left: 4px solid var(--warn); }
div[class*="st-key-box-rz"] { border-left: 4px solid var(--accent); }
div[class*="st-key-box-ms"] { border: 1px dashed var(--box-border); }
.merkkasten {
  background: var(--box-bg); border-left: 4px solid var(--teal);
  border-radius: 8px; padding: 0.9rem 1.1rem; margin: 0.6rem 0;
}
.warnbox {
  background: var(--box-bg); border-left: 4px solid var(--warn);
  border-radius: 8px; padding: 0.9rem 1.1rem; margin: 0.6rem 0;
}
.rezept {
  background: var(--box-bg); border-left: 4px solid var(--accent);
  border-radius: 8px; padding: 0.9rem 1.1rem; margin: 0.6rem 0;
}
.muster {
  background: var(--box-bg); border: 1px dashed var(--box-border);
  border-radius: 8px; padding: 0.9rem 1.1rem; margin: 0.6rem 0;
}
.kicker {
  text-transform: uppercase; letter-spacing: 0.14em; font-size: 0.72rem;
  color: var(--muted); margin-bottom: 0.15rem;
}
.pill {
  display: inline-block; background: var(--box-bg); border: 1px solid var(--box-border);
  border-radius: 999px; padding: 0.15rem 0.7rem; font-size: 0.78rem;
  margin-right: 0.35rem; color: var(--muted);
}
.pill-hot { border-color: var(--accent); color: var(--accent); }
</style>
"""

LIGHT_CSS = DARK_CSS.replace("#1B222C", "#F4F6F8").replace("#2E3947", "#D7DDE4")

# ----------------------------------------------------------------------------
# Session State
# ----------------------------------------------------------------------------

TOPICS = [
    "Komplexe Zahlen",
    "Folgen und Reihen",
    "Vollständige Induktion",
    "Differentialrechnung",
    "Integralrechnung",
    "Differentialgleichungen",
]

# Klausur-Gewichtung laut Dozenten-Hinweisen (für Adaptivität & Prüfungsmodus)
EXAM_WEIGHT = {
    "Integralrechnung": 3.0,
    "Folgen und Reihen": 2.5,
    "Vollständige Induktion": 2.0,
    "Komplexe Zahlen": 2.0,
    "Differentialrechnung": 1.5,
    "Differentialgleichungen": 1.0,
}

def init_state():
    ss = st.session_state
    ss.setdefault("dark_mode", True)
    ss.setdefault("done_sections", {})            # {topic: set(section)}
    ss.setdefault("quiz_stats", {t: {"richtig": 0, "falsch": 0} for t in TOPICS})
    ss.setdefault("fehlerheft", [])               # Liste von Strings
    ss.setdefault("exam", None)                   # aktueller Prüfungslauf
    ss.setdefault("quiz_task", None)              # aktuelle Quizaufgabe
    ss.setdefault("quiz_solved", False)

init_state()
st.markdown(DARK_CSS if st.session_state.dark_mode else LIGHT_CSS, unsafe_allow_html=True)

# ----------------------------------------------------------------------------
# UI-Bausteine
# ----------------------------------------------------------------------------

import itertools
_BOX_COUNTER = itertools.count()

def _boxify(md: str) -> str:
    """HTML-Reste in Markdown umwandeln, damit KaTeX ($…$) rendert."""
    return (md.replace("<b>", "**").replace("</b>", "**")
              .replace("<i>", "*").replace("</i>", "*")
              .replace("&nbsp;", "\u00A0")
              .replace("<br><br>", "\n\n").replace("<br>", "  \n"))

def _box(md: str, titel: str, icon: str, kind: str):
    with st.container(key=f"box-{kind}-{next(_BOX_COUNTER)}"):
        st.markdown(f"**{icon} {titel}**  \n{_boxify(md)}")

def merkkasten(md: str, titel: str = "Merkkasten"):
    _box(md, titel, "🧠", "mk")

def warnbox(md: str, titel: str = "Typischer Fehler"):
    _box(md, titel, "⚠️", "wb")

def rezept(md: str, titel: str = "Kochrezept"):
    _box(md, titel, "👩‍🍳", "rz")

def musterbox(md: str, titel: str = "Mustererkennung — Wenn … dann …"):
    _box(md, titel, "🔍", "ms")

def kicker(text: str):
    st.markdown(f'<div class="kicker">{text}</div>', unsafe_allow_html=True)

def klausur_pill(hot: bool, text: str):
    cls = "pill pill-hot" if hot else "pill"
    st.markdown(f'<span class="{cls}">{text}</span>', unsafe_allow_html=True)

def section_done_checkbox(topic: str, section: str):
    """Fortschritts-Häkchen am Ende eines Abschnitts."""
    key = f"done::{topic}::{section}"
    done_set = st.session_state.done_sections.setdefault(topic, set())
    checked = st.checkbox(f"✅ Abschnitt „{section}“ sitzt", value=section in done_set, key=key)
    if checked:
        done_set.add(section)
    else:
        done_set.discard(section)

def aufgabe(nr: str, stellung_md: str, latex_stellung: str | None,
            loesung_steps: list[tuple[str, str | None]], schwierigkeit: str = "●●○"):
    """Aufgabe mit ein-/ausblendbarer Schritt-für-Schritt-Lösung.
    loesung_steps: Liste aus (Markdown-Erklärung, optional LaTeX)."""
    with st.container(border=True):
        st.markdown(f"**Aufgabe {nr}** &nbsp; <span class='pill'>{schwierigkeit}</span>",
                    unsafe_allow_html=True)
        st.markdown(stellung_md)
        if latex_stellung:
            st.latex(latex_stellung)
        with st.expander("📝 Schritt-für-Schritt-Lösung anzeigen"):
            for i, (erkl, ltx) in enumerate(loesung_steps, 1):
                st.markdown(f"**Schritt {i}.** {erkl}")
                if ltx:
                    st.latex(ltx)

def record_quiz(topic: str, correct: bool, beschreibung: str = ""):
    stats = st.session_state.quiz_stats[topic]
    if correct:
        stats["richtig"] += 1
    else:
        stats["falsch"] += 1
        if beschreibung:
            st.session_state.fehlerheft.append(
                f"{datetime.now().strftime('%d.%m. %H:%M')} · {topic}: {beschreibung}")

def topic_error_rate(topic: str) -> float:
    s = st.session_state.quiz_stats[topic]
    n = s["richtig"] + s["falsch"]
    return (s["falsch"] + 1) / (n + 2)   # Laplace-Glättung

def gesamt_fortschritt() -> float:
    total_sections = 6 * len(TOPICS)  # 6 Kernabschnitte pro Thema
    done = sum(len(v) for v in st.session_state.done_sections.values())
    return min(1.0, done / total_sections)

# ----------------------------------------------------------------------------
# Aufgaben-Generatoren (zufällige, parametrisierte Klausuraufgaben)
# Jede Funktion liefert ein dict:
#   {"topic", "frage_md", "latex", "typ": "num"|"mc", "antwort", "optionen",
#    "toleranz", "loesung_md", "loesung_latex", "punkte"}
# ----------------------------------------------------------------------------

def gen_folgen_epsilon(rng: random.Random):
    """Typ Aufgabe 34: a_n = (c·n + d)/(n + e), Grenzwert c, N zu ε bestimmen."""
    c = rng.choice([1, 2, 3])
    e = rng.choice([1, 2, 3, 5])
    diff = rng.choice([2, 3, 4, 6])          # |d - c·e|
    d = c * e + diff
    eps = rng.choice([0.1, 0.01])
    # |a_n - c| = diff/(n+e) < eps  <=>  n > diff/eps - e
    schranke = diff / eps - e
    N = math.floor(schranke) + 1
    return {
        "topic": "Folgen und Reihen",
        "frage_md": (f"Gegeben ist die Folge mit dem Grenzwert $a={c}$. "
                     f"Bestimme den **kleinsten Index** $N$, sodass "
                     f"$|a_n - {c}| < \\varepsilon$ für alle $n \\ge N$ mit "
                     f"$\\varepsilon = {str(eps).replace('.', '{,}')}$ gilt."),
        "latex": rf"a_n = \frac{{{c}n + {d}}}{{n + {e}}}",
        "typ": "num", "antwort": float(N), "toleranz": 0.0, "punkte": 6,
        "loesung_md": (f"$|a_n - {c}| = \\dfrac{{{diff}}}{{n+{e}}} < {eps}$ "
                       f"⟹ $n + {e} > {diff}/{eps} = {diff/eps:g}$ "
                       f"⟹ $n > {schranke:g}$ ⟹ **N = {N}**."),
        "loesung_latex": rf"\left|\frac{{{c}n+{d}}}{{n+{e}}} - {c}\right| = \frac{{{diff}}}{{n+{e}}}",
    }

def gen_folgen_grenzwert(rng: random.Random):
    a = rng.randint(1, 5); b = rng.randint(1, 9)
    c = rng.randint(1, 5); d = rng.randint(1, 9)
    gw = a / c
    return {
        "topic": "Folgen und Reihen",
        "frage_md": "Bestimme den Grenzwert der Folge (als Dezimalzahl, 3 Nachkommastellen genügen):",
        "latex": rf"a_n = \frac{{{a}n^2 + {b}n}}{{{c}n^2 + {d}}}",
        "typ": "num", "antwort": gw, "toleranz": 0.005, "punkte": 3,
        "loesung_md": (f"Höchste Potenz $n^2$ ausklammern und kürzen ⟹ "
                       f"Grenzwert $= {a}/{c} = {gw:g}$."),
        "loesung_latex": rf"\lim_{{n\to\infty}} \frac{{{a} + {b}/n}}{{{c} + {d}/n^2}} = \frac{{{a}}}{{{c}}}",
    }

def gen_induktion_mc(rng: random.Random):
    variante = rng.choice(["anfang", "teilbar"])
    if variante == "anfang":
        n0 = 1
        richtig = f"n = {n0} einsetzen und beide Seiten getrennt ausrechnen"
        optionen = [
            richtig,
            "Die Behauptung für n+1 aufschreiben",
            "Die Induktionsvoraussetzung beweisen",
            "n gegen unendlich laufen lassen",
        ]
        return {
            "topic": "Vollständige Induktion",
            "frage_md": ("Beim Beweis von $\\sum_{k=1}^{n} k = \\frac{n(n+1)}{2}$: "
                         "Was passiert im **Induktionsanfang**?"),
            "latex": None, "typ": "mc", "antwort": richtig,
            "optionen": optionen, "punkte": 2,
            "loesung_md": ("Im Induktionsanfang wird die Aussage für das kleinste n "
                           "(hier $n=1$) **nachgerechnet**: links $1$, rechts "
                           "$\\frac{1\\cdot 2}{2} = 1$. ✓"),
            "loesung_latex": None,
        }
    else:
        richtig = r"8^{n+1}-1 = 8\cdot(8^n - 1) + 7"
        optionen = [
            richtig,
            r"8^{n+1}-1 = 8^n \cdot 8^n - 1",
            r"8^{n+1}-1 = (8^n-1)+1",
            r"8^{n+1}-1 = 8\cdot 8^n + 7",
        ]
        return {
            "topic": "Vollständige Induktion",
            "frage_md": ("Beweis: $7 \\mid 8^n - 1$. Welche Umformung macht die "
                         "**Induktionsvoraussetzung einsetzbar**?"),
            "latex": None, "typ": "mc", "antwort": richtig,
            "optionen": optionen, "punkte": 3,
            "loesung_md": ("$8^{n+1}-1 = 8\\cdot 8^n - 8 + 7 = 8(8^n-1)+7$. "
                           "Beide Summanden sind durch 7 teilbar (IV bzw. offensichtlich). ∎"),
            "loesung_latex": None,
        }

def gen_integration_sinus(rng: random.Random):
    a = rng.choice([2, 3, 4, 5])
    richtig = rf"-\ln(\cos x + {a}) + C"
    optionen = [
        richtig,
        rf"\ln(\cos x + {a}) + C",
        rf"-\dfrac{{\cos x}}{{(\cos x + {a})^2}} + C",
        rf"\dfrac{{\sin^2 x}}{{2(\cos x+{a})}} + C",
    ]
    return {
        "topic": "Integralrechnung",
        "frage_md": "**Der angekündigte Klausurtyp** — Sinus im Zähler, Funktion im Nenner:",
        "latex": rf"\int \frac{{\sin x}}{{\cos x + {a}}}\,dx = \;?",
        "typ": "mc", "antwort": richtig, "optionen": optionen, "punkte": 5,
        "loesung_md": (f"Substitution $u = \\cos x + {a}$ ⟹ $du = -\\sin x\\,dx$. "
                       f"Der Zähler ist (bis aufs Vorzeichen) die Ableitung des Nenners "
                       f"⟹ $-\\int \\frac{{du}}{{u}} = -\\ln|u| + C$. "
                       f"Da $\\cos x + {a} > 0$, entfällt der Betrag."),
        "loesung_latex": rf"-\ln(\cos x + {a}) + C",
    }

def gen_integration_pbz(rng: random.Random):
    while True:
        p = rng.choice([-3, -2, -1, 1, 2, 3])
        q = rng.choice([-3, -2, -1, 1, 2, 3])
        if p != q:
            break
    A = rng.randint(1, 4); B = rng.randint(1, 4)
    m = A + B
    c = -(A * q + B * p)
    return {
        "topic": "Integralrechnung",
        "frage_md": (f"Partialbruchzerlegung: Bestimme **A** im Ansatz "
                     f"$\\dfrac{{A}}{{x - ({p})}} + \\dfrac{{B}}{{x - ({q})}}$ für"),
        "latex": rf"\frac{{{m}x + ({c})}}{{(x - ({p}))(x - ({q}))}}",
        "typ": "num", "antwort": float(A), "toleranz": 0.001, "punkte": 5,
        "loesung_md": (f"Zuhaltemethode: $x = {p}$ einsetzen in "
                       f"$\\dfrac{{{m}x + ({c})}}{{x - ({q})}}$ ⟹ "
                       f"$A = \\dfrac{{{m}\\cdot({p}) + ({c})}}{{{p} - ({q})}} = {A}$. "
                       f"(Analog $B = {B}$.)"),
        "loesung_latex": None,
    }

def gen_komplex_betrag(rng: random.Random):
    a, b, r = rng.choice([(3, 4, 5), (6, 8, 10), (5, 12, 13), (8, 15, 17), (0, 7, 7)])
    if rng.random() < 0.5:
        a, b = b, a
    sa = rng.choice([1, -1]); sb = rng.choice([1, -1])
    a *= sa; b *= sb
    return {
        "topic": "Komplexe Zahlen",
        "frage_md": "Berechne den Betrag $|z|$ von",
        "latex": rf"z = {a} {'+' if b >= 0 else '-'} {abs(b)}i",
        "typ": "num", "antwort": float(r), "toleranz": 0.001, "punkte": 2,
        "loesung_md": f"$|z| = \\sqrt{{({a})^2 + ({b})^2}} = \\sqrt{{{a*a + b*b}}} = {r}$.",
        "loesung_latex": None,
    }

def gen_komplex_menge(rng: random.Random):
    z0a = rng.randint(-2, 2); z0b = rng.randint(-2, 2); r = rng.randint(1, 3)
    richtig = f"Kreisscheibe (ohne Rand) um {z0a}{'+' if z0b>=0 else '-'}{abs(z0b)}i mit Radius {r}"
    optionen = [
        richtig,
        f"Kreislinie um {z0a}{'+' if z0b>=0 else '-'}{abs(z0b)}i mit Radius {r}",
        f"Alles außerhalb des Kreises mit Radius {r}",
        "Eine Gerade (Mittelsenkrechte)",
    ]
    return {
        "topic": "Komplexe Zahlen",
        "frage_md": "**Mengen zeichnen (Klausur-Fokus!):** Welche Menge beschreibt",
        "latex": rf"M = \{{\, z \in \mathbb{{C}} : |z - ({z0a} {'+' if z0b>=0 else '-'} {abs(z0b)}i)| < {r} \,\}}",
        "typ": "mc", "antwort": richtig, "optionen": optionen, "punkte": 3,
        "loesung_md": ("$|z - z_0| < r$ = alle Punkte mit Abstand **kleiner** $r$ vom "
                       "Mittelpunkt $z_0$ ⟹ offene Kreisscheibe. "
                       "($=r$: Kreislinie, $>r$: Äußeres, $|z-a|=|z-b|$: Mittelsenkrechte.)"),
        "loesung_latex": None,
    }

def gen_ableitung(rng: random.Random):
    a = rng.randint(1, 3); b = rng.randint(1, 5); x0 = rng.randint(-2, 2)
    wert = 3 * a * x0**2 - b
    return {
        "topic": "Differentialrechnung",
        "frage_md": f"Berechne $f'({x0})$ für",
        "latex": rf"f(x) = {a}x^3 - {b}x",
        "typ": "num", "antwort": float(wert), "toleranz": 0.001, "punkte": 2,
        "loesung_md": f"$f'(x) = {3*a}x^2 - {b}$ ⟹ $f'({x0}) = {3*a}\\cdot{x0**2} - {b} = {wert}$.",
        "loesung_latex": None,
    }

def gen_dgl_mc(rng: random.Random):
    k = rng.choice([2, 3, -1, -2]); y0 = rng.choice([1, 2, 4])
    richtig = rf"y(x) = {y0}\,e^{{{k}x}}"
    optionen = [
        richtig,
        rf"y(x) = {y0} + e^{{{k}x}}",
        rf"y(x) = e^{{{k}x}} + {y0}x",
        rf"y(x) = {y0}\,e^{{x}} + {k}",
    ]
    return {
        "topic": "Differentialgleichungen",
        "frage_md": f"Löse das Anfangswertproblem $y' = {k}y$, $\\;y(0) = {y0}$:",
        "latex": None, "typ": "mc", "antwort": richtig, "optionen": optionen, "punkte": 3,
        "loesung_md": (f"Trennung der Variablen: $\\int \\frac{{dy}}{{y}} = \\int {k}\\,dx$ "
                       f"⟹ $\\ln|y| = {k}x + c$ ⟹ $y = C e^{{{k}x}}$. "
                       f"AWP: $y(0) = C = {y0}$."),
        "loesung_latex": None,
    }

GENERATORS = {
    "Folgen und Reihen": [gen_folgen_epsilon, gen_folgen_grenzwert],
    "Vollständige Induktion": [gen_induktion_mc],
    "Integralrechnung": [gen_integration_sinus, gen_integration_pbz],
    "Komplexe Zahlen": [gen_komplex_betrag, gen_komplex_menge],
    "Differentialrechnung": [gen_ableitung],
    "Differentialgleichungen": [gen_dgl_mc],
}

def neue_aufgabe(topic: str | None = None, rng: random.Random | None = None):
    rng = rng or random.Random()
    if topic is None:
        # adaptiv: Fehlerquote × Klausurgewicht
        weights = [topic_error_rate(t) * EXAM_WEIGHT[t] for t in TOPICS]
        topic = rng.choices(TOPICS, weights=weights, k=1)[0]
    gen = rng.choice(GENERATORS[topic])
    task = gen(rng)
    if task["typ"] == "mc":
        opts = task["optionen"][:]
        rng.shuffle(opts)
        task["optionen"] = opts
    return task

def render_task_input(task: dict, key: str):
    """Zeigt Aufgabe + Eingabefeld, gibt (beantwortet, korrekt) zurück."""
    st.markdown(task["frage_md"])
    if task.get("latex"):
        st.latex(task["latex"])
    if task["typ"] == "num":
        val = st.number_input("Deine Antwort", value=None, step=0.001,
                              format="%.3f", key=f"{key}_num",
                              placeholder="Zahl eingeben …")
        return val
    else:
        # MC: LaTeX-Optionen als radio mit index, Anzeige via st.latex
        labels = [f"Antwort {chr(65+i)}" for i in range(len(task["optionen"]))]
        for lab, opt in zip(labels, task["optionen"]):
            c1, c2 = st.columns([1, 8])
            with c1:
                st.markdown(f"**{lab}**")
            with c2:
                if any(ch in opt for ch in "\\^_{"):
                    st.latex(opt)
                else:
                    st.markdown(opt)
        wahl = st.radio("Deine Antwort", labels, index=None, horizontal=True,
                        key=f"{key}_mc")
        if wahl is None:
            return None
        return task["optionen"][labels.index(wahl)]

def check_task(task: dict, eingabe) -> bool:
    if eingabe is None:
        return False
    if task["typ"] == "num":
        return abs(float(eingabe) - task["antwort"]) <= task.get("toleranz", 0.001)
    return eingabe == task["antwort"]

# ----------------------------------------------------------------------------
# Plots
# ----------------------------------------------------------------------------

def plot_komplexe_menge(art: str):
    fig, ax = plt.subplots(figsize=(4.6, 4.6))
    fig.patch.set_alpha(0); ax.set_facecolor("none")
    xs = np.linspace(-4, 4, 400)
    ax.axhline(0, color="#9AA5B1", lw=0.8); ax.axvline(0, color="#9AA5B1", lw=0.8)
    if art == "|z - (1+i)| < 2  (offene Kreisscheibe)":
        circ = plt.Circle((1, 1), 2, color="#4FD1C5", alpha=0.25)
        ax.add_patch(circ)
        ax.add_patch(plt.Circle((1, 1), 2, fill=False, color="#4FD1C5", ls="--", lw=2))
        ax.plot(1, 1, "o", color="#FFD166"); ax.annotate("z₀ = 1+i", (1.1, 1.1), color="#FFD166")
    elif art == "|z - 2| = 1,5  (Kreislinie)":
        ax.add_patch(plt.Circle((2, 0), 1.5, fill=False, color="#4FD1C5", lw=2.5))
        ax.plot(2, 0, "o", color="#FFD166")
    elif art == "Re(z) ≥ 1  (Halbebene)":
        ax.fill_betweenx([-4, 4], 1, 4, color="#4FD1C5", alpha=0.25)
        ax.axvline(1, color="#4FD1C5", lw=2)
    elif art == "|z - 1| = |z + 1|  (Mittelsenkrechte)":
        ax.axvline(0, color="#4FD1C5", lw=2.5)
        ax.plot([1, -1], [0, 0], "o", color="#FFD166")
        ax.annotate("gleicher Abstand zu 1 und −1", (0.15, 3.0), color="#9AA5B1")
    else:  # Sektor
        th = np.linspace(np.pi/6, np.pi/3, 60)
        rr = np.linspace(0, 4, 2)
        for r_ in [4]:
            ax.fill(np.concatenate([[0], r_*np.cos(th), [0]]),
                    np.concatenate([[0], r_*np.sin(th), [0]]),
                    color="#4FD1C5", alpha=0.25)
        for ang in [np.pi/6, np.pi/3]:
            ax.plot([0, 4*np.cos(ang)], [0, 4*np.sin(ang)], color="#4FD1C5", lw=2)
    ax.set_xlim(-4, 4); ax.set_ylim(-4, 4); ax.set_aspect("equal")
    ax.set_xlabel("Re(z)"); ax.set_ylabel("Im(z)")
    for spine in ax.spines.values():
        spine.set_color("#2E3947")
    ax.tick_params(colors="#9AA5B1")
    ax.xaxis.label.set_color("#9AA5B1"); ax.yaxis.label.set_color("#9AA5B1")
    ax.grid(alpha=0.15)
    return fig

def plot_sin_cos():
    x = np.linspace(-2*np.pi, 2*np.pi, 500)
    fig, ax = plt.subplots(figsize=(7.5, 3.2))
    fig.patch.set_alpha(0); ax.set_facecolor("none")
    ax.plot(x, np.sin(x), color="#4FD1C5", lw=2, label="sin(x) — ungerade (punktsym.)")
    ax.plot(x, np.cos(x), color="#FFD166", lw=2, label="cos(x) — gerade (achsensym.)")
    ax.axhline(0, color="#9AA5B1", lw=0.8); ax.axvline(0, color="#9AA5B1", lw=0.8)
    ax.legend(facecolor="none", labelcolor="#E8EAED", edgecolor="#2E3947")
    for spine in ax.spines.values():
        spine.set_color("#2E3947")
    ax.tick_params(colors="#9AA5B1"); ax.grid(alpha=0.15)
    return fig

# ----------------------------------------------------------------------------
# Mini-Quiz-Block (pro Thema) & Adaptives Quiz
# ----------------------------------------------------------------------------

def mini_quiz(topic: str):
    st.subheader("🎯 Mini-Quiz")
    st.caption("Zufallsaufgaben mit sofortigem Feedback — Ergebnisse fließen in die adaptive Wiederholung ein.")
    key = f"mini_{topic}"
    if st.session_state.get(f"{key}_task") is None:
        st.session_state[f"{key}_task"] = neue_aufgabe(topic)
        st.session_state[f"{key}_done"] = False
    task = st.session_state[f"{key}_task"]
    eingabe = render_task_input(task, key)
    c1, c2 = st.columns([1, 1])
    if c1.button("Prüfen", key=f"{key}_check", type="primary",
                 disabled=st.session_state[f"{key}_done"]):
        if eingabe is None:
            st.warning("Bitte erst eine Antwort eingeben/auswählen.")
        else:
            ok = check_task(task, eingabe)
            record_quiz(topic, ok, task["frage_md"][:60])
            st.session_state[f"{key}_done"] = True
            st.session_state[f"{key}_ok"] = ok
    if st.session_state.get(f"{key}_done"):
        if st.session_state.get(f"{key}_ok"):
            st.success("✅ Richtig!")
        else:
            st.error("❌ Leider falsch — schau dir die Lösung genau an (→ Fehlerheft).")
        st.markdown("**Musterlösung:** " + task["loesung_md"])
        if task.get("loesung_latex"):
            st.latex(task["loesung_latex"])
    if c2.button("Nächste Aufgabe →", key=f"{key}_next"):
        st.session_state[f"{key}_task"] = neue_aufgabe(topic)
        st.session_state[f"{key}_done"] = False
        st.rerun()

# ----------------------------------------------------------------------------
# THEMA 1: Komplexe Zahlen
# ----------------------------------------------------------------------------

def seite_komplex():
    kicker("Thema 1 · Klausur-Fokus: Mengen zeichnen")
    st.title("Komplexe Zahlen")
    klausur_pill(True, "🔥 Mengen zeichnen (angekündigt)")
    klausur_pill(False, "Polarform"); klausur_pill(False, "De Moivre")

    tabs = st.tabs(["💡 Intuition", "📖 Theorie", "🧠 Merkregeln",
                    "✏️ Klausuraufgaben", "🖊️ Mengen zeichnen", "🧮 Rechner", "🎯 Quiz"])

    with tabs[0]:
        st.markdown("""
Stell dir die komplexen Zahlen als **Erweiterung des Zahlenstrahls zu einer Ebene** vor:
Jede Zahl $z = a + bi$ ist ein *Punkt* mit Koordinaten $(a, b)$ — Realteil nach rechts,
Imaginärteil nach oben. Das $i$ ist dabei nichts Mystisches, sondern schlicht die Zahl
mit der Eigenschaft $i^2 = -1$.

Zwei Sichtweisen auf denselben Punkt:
- **Kartesisch** ($a + bi$): gut zum **Addieren** (wie Vektoren aneinanderhängen)
- **Polar** ($r \\cdot e^{i\\varphi}$): gut zum **Multiplizieren** — Beträge multiplizieren,
  Winkel addieren. Multiplikation ist also *Drehstreckung*.

Deshalb ist De Moivre keine neue Regel, sondern nur: „$n$-mal drehen und strecken“.
""")
        section_done_checkbox("Komplexe Zahlen", "Intuition")

    with tabs[1]:
        st.markdown("**Definitionen & Rechenregeln** (für $z = a+bi,\\ w = c+di$):")
        st.latex(r"z \pm w = (a \pm c) + (b \pm d)i")
        st.latex(r"z \cdot w = (ac - bd) + (ad + bc)i")
        st.latex(r"\frac{z}{w} = \frac{z \cdot \overline{w}}{|w|^2} = \frac{(a+bi)(c-di)}{c^2+d^2}")
        st.latex(r"\overline{z} = a - bi, \qquad |z| = \sqrt{a^2+b^2} = \sqrt{z\overline{z}}")
        st.markdown("**Polar- und Exponentialform:**")
        st.latex(r"z = r(\cos\varphi + i\sin\varphi) = r\,e^{i\varphi}, \quad r = |z|,\ \ \tan\varphi = \tfrac{b}{a}\ (\text{Quadrant beachten!})")
        st.markdown("**Potenzen (De Moivre) und Wurzeln:**")
        st.latex(r"z^n = r^n e^{in\varphi}")
        st.latex(r"z_k = \sqrt[n]{r}\;e^{\,i\frac{\varphi + 2\pi k}{n}}, \quad k = 0, 1, \dots, n-1")
        st.markdown("Die $n$ Wurzeln liegen als **regelmäßiges n-Eck** auf einem Kreis mit Radius $\\sqrt[n]{r}$.")
        section_done_checkbox("Komplexe Zahlen", "Theorie")

    with tabs[2]:
        merkkasten("""
• Division = <b>mit dem konjugierten Nenner erweitern</b> (macht den Nenner reell).<br>
• Multiplizieren in Polarform: <b>Beträge mal, Winkel plus</b>.<br>
• Argument: erst $\\tan\\varphi = b/a$, dann <b>Quadrant prüfen</b> (Skizze!).<br>
• $i^1=i,\\ i^2=-1,\\ i^3=-i,\\ i^4=1$ — Viererzyklus.<br>
• $n$-te Wurzeln: <b>immer n Stück</b>, Winkelabstand $2\\pi/n$.""")
        warnbox("""
1. <b>Quadrantenfehler beim Argument</b>: $z=-1+i$ liegt im 2. Quadranten ⟹ $\\varphi = 3\\pi/4$, nicht $-\\pi/4$!<br>
2. Beim Dividieren vergessen, <b>auch den Zähler</b> mit $\\overline{w}$ zu multiplizieren.<br>
3. Bei Wurzeln nur $k=0$ angeben — es gibt aber $n$ Lösungen.""")
        section_done_checkbox("Komplexe Zahlen", "Merkregeln")

    with tabs[3]:
        aufgabe("K1", "Berechne $\\dfrac{3+4i}{1-2i}$ und gib das Ergebnis in der Form $a+bi$ an.", None, [
            ("Mit dem konjugierten Nenner $1+2i$ erweitern:",
             r"\frac{(3+4i)(1+2i)}{(1-2i)(1+2i)}"),
            ("Nenner: $1^2 + 2^2 = 5$ (dritte binomische Formel).", None),
            ("Zähler ausmultiplizieren: $3 + 6i + 4i + 8i^2 = 3 + 10i - 8 = -5 + 10i$.", None),
            ("Ergebnis:", r"\frac{-5+10i}{5} = -1 + 2i"),
            ("Kontrolle: $(-1+2i)(1-2i) = -1+2i+2i-4i^2 = 3+4i$ ✓", None),
        ], "●○○")
        aufgabe("K2", "Bringe $z = -1 + i$ in Exponentialform und berechne $z^8$.", None, [
            ("Betrag:", r"r = \sqrt{(-1)^2 + 1^2} = \sqrt{2}"),
            ("Argument: Punkt $(-1, 1)$ liegt im **2. Quadranten** ⟹ $\\varphi = \\pi - \\pi/4 = 3\\pi/4$.", None),
            ("Also:", r"z = \sqrt{2}\, e^{i\,3\pi/4}"),
            ("De Moivre:", r"z^8 = (\sqrt{2})^8 e^{i\,6\pi} = 16 \cdot e^{i\cdot 0} = 16"),
            ("Kontrolle: $z^2 = (-1+i)^2 = -2i$, $z^4 = (-2i)^2 = -4$, $z^8 = 16$ ✓", None),
        ], "●●○")
        aufgabe("K3", "Bestimme alle Lösungen von $z^3 = 8i$.", None, [
            ("Rechte Seite in Polarform: $8i = 8\\,e^{i\\pi/2}$.", None),
            ("Wurzelformel mit $n=3$:", r"z_k = 2\,e^{\,i\frac{\pi/2 + 2\pi k}{3}}, \quad k = 0,1,2"),
            ("Die drei Winkel: $\\pi/6$, $5\\pi/6$, $3\\pi/2$.", None),
            ("Kartesisch:", r"z_0 = \sqrt{3} + i,\quad z_1 = -\sqrt{3} + i,\quad z_2 = -2i"),
            ("Skizze: gleichseitiges Dreieck auf dem Kreis mit Radius 2. ✓", None),
        ], "●●●")
        section_done_checkbox("Komplexe Zahlen", "Klausuraufgaben")

    with tabs[4]:
        st.markdown("**Der angekündigte Klausurteil.** Übersetze die Bedingung in Geometrie:")
        musterbox("""
<b>Wenn</b> $|z - z_0| = r$ <b>dann</b> Kreislinie um $z_0$ mit Radius $r$.<br>
<b>Wenn</b> $|z - z_0| < r$ <b>dann</b> offene Kreisscheibe (Rand gestrichelt!).<br>
<b>Wenn</b> $|z - z_0| \\ge r$ <b>dann</b> Äußeres inkl. Rand.<br>
<b>Wenn</b> $|z - a| = |z - b|$ <b>dann</b> Mittelsenkrechte zwischen $a$ und $b$.<br>
<b>Wenn</b> $\\mathrm{Re}(z) \\ge c$ / $\\mathrm{Im}(z) \\le c$ <b>dann</b> Halbebene.<br>
<b>Wenn</b> $\\alpha \\le \\arg(z) \\le \\beta$ <b>dann</b> Winkelsektor ab Ursprung.""")
        wahl = st.selectbox("Beispiel auswählen:", [
            "|z - (1+i)| < 2  (offene Kreisscheibe)",
            "|z - 2| = 1,5  (Kreislinie)",
            "Re(z) ≥ 1  (Halbebene)",
            "|z - 1| = |z + 1|  (Mittelsenkrechte)",
            "π/6 ≤ arg(z) ≤ π/3  (Sektor)",
        ])
        st.pyplot(plot_komplexe_menge(wahl))
        warnbox("""In der Klausur: <b>Rand gestrichelt</b> bei $<$ oder $>$,
<b>durchgezogen</b> bei $\\le,\\ \\ge,\\ =$. Mittelpunkt beschriften, Radius einzeichnen!""")
        section_done_checkbox("Komplexe Zahlen", "Mengen zeichnen")

    with tabs[5]:
        st.markdown("**Interaktiver Umrechner: kartesisch ⟷ polar**")
        c1, c2 = st.columns(2)
        a = c1.number_input("Realteil a", value=-1.0, step=0.5)
        b = c2.number_input("Imaginärteil b", value=1.0, step=0.5)
        r = math.hypot(a, b)
        phi = math.atan2(b, a)
        st.latex(rf"z = {a:g} {'+' if b >= 0 else '-'} {abs(b):g}i"
                 rf"\;=\; {r:.4g}\,e^{{i \cdot {phi:.4g}}}"
                 rf"\quad (\varphi = {math.degrees(phi):.2f}^\circ)")
        st.caption("Beachte: atan2 liefert automatisch den richtigen Quadranten — "
                   "in der Klausur musst du das per Skizze selbst prüfen!")
        section_done_checkbox("Komplexe Zahlen", "Rechner")

    with tabs[6]:
        mini_quiz("Komplexe Zahlen")

# ----------------------------------------------------------------------------
# THEMA 2: Folgen und Reihen
# ----------------------------------------------------------------------------

def seite_folgen():
    kicker("Thema 2 · Klausur-Fokus: Folgen + Abschätzung (Aufgabe 34!)")
    st.title("Folgen und Reihen")
    klausur_pill(True, "🔥 Aufgabe 34 (explizit angekündigt)")
    klausur_pill(True, "🔥 ε-Abschätzung (10 % / 1 %)")
    klausur_pill(False, "Reihen: laut Dozent kaum relevant")

    tabs = st.tabs(["💡 Intuition", "📖 Theorie", "🧠 Merkregeln",
                    "⭐ Aufgabe 34 komplett", "✏️ Weitere Aufgaben", "🧮 ε-N-Rechner", "🎯 Quiz"])

    with tabs[0]:
        st.markdown("""
Eine Folge ist eine **unendliche Liste von Zahlen** $a_1, a_2, a_3, \\dots$ —
und Konvergenz beantwortet die Frage: *„Pendelt sich die Liste bei einem Wert ein?“*

Die formale Definition ist ein **Spiel**: Ein Gegner nennt dir eine beliebig kleine
Toleranz $\\varepsilon$ (z. B. 1 %). Du gewinnst, wenn du einen Index $N$ nennen kannst,
ab dem **alle** Folgenglieder näher als $\\varepsilon$ am Grenzwert liegen.
Genau dieses Spiel ist Aufgabe 34: Der Gegner sagt $\\varepsilon = 0{,}01$ — du lieferst $N$.
""")
        section_done_checkbox("Folgen und Reihen", "Intuition")

    with tabs[1]:
        st.markdown("**Konvergenzdefinition:**")
        st.latex(r"\lim_{n\to\infty} a_n = a \;:\Longleftrightarrow\; \forall \varepsilon > 0\ \exists N \in \mathbb{N}:\ |a_n - a| < \varepsilon \quad \forall n \ge N")
        st.markdown("""
**Weitere Begriffe:**
- **Monoton wachsend:** $a_{n+1} \\ge a_n$ für alle $n$ (prüfe $a_{n+1} - a_n \\ge 0$ oder $\\frac{a_{n+1}}{a_n} \\ge 1$)
- **Beschränkt:** es gibt $S$ mit $|a_n| \\le S$
- **Satz:** monoton + beschränkt ⟹ konvergent
- **Grenzwertsätze:** Limes von Summe/Produkt/Quotient = Summe/Produkt/Quotient der Limites (Nenner ≠ 0)

**Standardgrenzwerte** (auswendig!):
""")
        st.latex(r"\frac{1}{n} \to 0, \qquad q^n \to 0 \ (|q|<1), \qquad \sqrt[n]{n} \to 1, \qquad \sqrt[n]{c} \to 1, \qquad \left(1+\tfrac{1}{n}\right)^n \to e")
        section_done_checkbox("Folgen und Reihen", "Theorie")

    with tabs[2]:
        merkkasten("""
• Grenzwert gebrochen-rationaler Folgen: <b>höchste Potenz ausklammern</b> —
Zählergrad = Nennergrad ⟹ Quotient der Leitkoeffizienten.<br>
• Bei ε-Aufgaben <b>zuerst vereinfachen/faktorisieren</b>, dann Differenz bilden.<br>
• $|a_n - a|$ wird fast immer zu $\\frac{\\text{Konstante}}{n + \\text{etwas}}$ —
dann einfach nach $n$ auflösen.<br>
• ε = 10 % heißt 0,1 · ε = 1 % heißt 0,01.""")
        warnbox("""
1. <b>Betragsstriche vergessen</b> — erst zeigen, dass der Ausdruck positiv ist, dann weglassen.<br>
2. $n > 299$ bedeutet $N = 300$ (kleinste <b>natürliche</b> Zahl größer als die Schranke) —
nicht $N = 299$!<br>
3. Beim Faktorisieren die Definitionslücke übersehen ($n = 1$ beim Nenner $n^2 - 1$).""")
        section_done_checkbox("Folgen und Reihen", "Merkregeln")

    with tabs[3]:
        st.markdown("### ⭐ Aufgabe 34 — die angekündigte Klausuraufgabe")
        aufgabe("34", "Untersuche die Konvergenz, indem du einen Folgenindex $N$ bestimmst, "
                "sodass $|a_n - 1| < \\varepsilon$ für alle $n \\ge N$ mit $\\varepsilon = 0{,}01$:",
                r"a_n = \frac{n(n+3) - 4}{n^2 - 1}", [
            ("**Was erkenne ich?** Gebrochen-rational, Zähler- und Nennergrad gleich (2). "
             "Der Zähler lässt sich vielleicht faktorisieren — immer zuerst versuchen!", None),
            ("Zähler ausmultiplizieren und faktorisieren: $n^2 + 3n - 4 = (n+4)(n-1)$. "
             "Nenner: dritte binomische Formel.",
             r"a_n = \frac{(n+4)(n-1)}{(n-1)(n+1)} = \frac{n+4}{n+1} \quad (n \ge 2)"),
            ("**Grenzwert:** Zähler und Nenner wachsen gleich schnell ⟹ $a_n \\to 1$. "
             "(Formal: $\\frac{1 + 4/n}{1 + 1/n} \\to \\frac{1}{1} = 1$.)", None),
            ("**Differenz zum Grenzwert bilden** und auf einen Bruch bringen:",
             r"|a_n - 1| = \left|\frac{n+4}{n+1} - \frac{n+1}{n+1}\right| = \frac{3}{n+1}"),
            ("(Betrag darf weg, weil $\\frac{3}{n+1} > 0$ für alle $n \\in \\mathbb{N}$.)", None),
            ("**Ungleichung lösen:**",
             r"\frac{3}{n+1} < 0{,}01 \iff n + 1 > 300 \iff n > 299"),
            ("**Antwortsatz:** Für $N = 300$ gilt $|a_n - 1| < 0{,}01$ für alle $n \\ge N$. "
             "Die Folge konvergiert gegen 1. ∎", None),
            ("**Kontrolle:** $a_{300} = \\frac{304}{301} \\approx 1{,}00997 < 1{,}01$ ✓ "
             "und $a_{299} = \\frac{303}{300} = 1{,}01$ (nicht $< 0{,}01$ Abstand) ✓ — "
             "N = 300 ist also wirklich der kleinste Index.", None),
        ], "●●○")
        merkkasten("""Variante <b>ε = 0,1 (10 %)</b>: gleiche Rechnung,
$n + 1 > 30 \\iff n > 29 \\Rightarrow N = 30$.
Das Schema ist immer identisch: <b>faktorisieren → Grenzwert → Differenz → auflösen → Antwortsatz</b>.""",
        "Die 30 %/10 %-Variante")
        section_done_checkbox("Folgen und Reihen", "Aufgabe 34")

    with tabs[4]:
        aufgabe("F1", "Bestimme den Grenzwert:", r"a_n = \frac{2n^2 - 5n + 1}{4n^2 + n}", [
            ("Höchste Potenz $n^2$ in Zähler und Nenner ausklammern:",
             r"a_n = \frac{2 - 5/n + 1/n^2}{4 + 1/n}"),
            ("Alle Brüche mit $n$ im Nenner gehen gegen 0:",
             r"\lim_{n\to\infty} a_n = \frac{2}{4} = \frac{1}{2}"),
        ], "●○○")
        aufgabe("F2", "Untersuche $a_n = \\dfrac{3n}{n+2}$ auf Monotonie und Beschränktheit "
                "und folgere die Konvergenz.", None, [
            ("Monotonie über die Differenz:",
             r"a_{n+1} - a_n = \frac{3(n+1)}{n+3} - \frac{3n}{n+2} = \frac{6}{(n+3)(n+2)} > 0"),
            ("⟹ streng monoton wachsend.", None),
            ("Beschränktheit: $a_n = \\frac{3n}{n+2} < \\frac{3n}{n} = 3$ ⟹ nach oben durch 3 beschränkt "
             "(nach unten durch $a_1 = 1$).", None),
            ("Monoton + beschränkt ⟹ konvergent. Grenzwert: $\\frac{3}{1} = 3$.", None),
        ], "●●○")
        aufgabe("F3", "Bestimme $N$ mit $|a_n - 2| < 0{,}1$ für $a_n = \\dfrac{2n + 7}{n + 1}$.", None, [
            ("Differenz bilden:",
             r"|a_n - 2| = \left|\frac{2n+7 - 2(n+1)}{n+1}\right| = \frac{5}{n+1}"),
            ("Auflösen:", r"\frac{5}{n+1} < 0{,}1 \iff n+1 > 50 \iff n > 49"),
            ("⟹ $N = 50$. ∎", None),
        ], "●●○")
        section_done_checkbox("Folgen und Reihen", "Weitere Aufgaben")

    with tabs[5]:
        st.markdown("**Interaktiver ε-N-Rechner** — für Folgen der Form $a_n = \\frac{cn+d}{n+e}$:")
        c1, c2, c3, c4 = st.columns(4)
        c = c1.number_input("c (Zähler)", value=1.0, step=1.0)
        d = c2.number_input("d (Zähler)", value=4.0, step=1.0)
        e = c3.number_input("e (Nenner)", value=1.0, step=1.0)
        eps = c4.selectbox("ε", [0.1, 0.01, 0.001], index=1)
        diff = abs(d - c * e)
        st.latex(rf"|a_n - {c:g}| = \frac{{{diff:g}}}{{n + {e:g}}} < {eps}")
        if diff == 0:
            st.info("Die Folge ist konstant gleich dem Grenzwert — jedes N funktioniert.")
        else:
            schranke = diff / eps - e
            N = math.floor(schranke) + 1
            st.latex(rf"n > {schranke:g} \;\Longrightarrow\; N = {N}")
            n_plot = np.arange(1, max(20, min(N + 10, 500)))
            fig, ax = plt.subplots(figsize=(7.5, 3))
            fig.patch.set_alpha(0); ax.set_facecolor("none")
            ax.plot(n_plot, (c * n_plot + d) / (n_plot + e), ".", ms=3, color="#4FD1C5", label="aₙ")
            ax.axhline(c, color="#FFD166", lw=1.2, label="Grenzwert")
            ax.axhline(c + eps, color="#F6AD55", lw=0.9, ls="--", label="ε-Schlauch")
            ax.axhline(c - eps, color="#F6AD55", lw=0.9, ls="--")
            if N < 500:
                ax.axvline(N, color="#FC8181", lw=1.2, ls=":", label=f"N = {N}")
            ax.legend(facecolor="none", labelcolor="#E8EAED", edgecolor="#2E3947", fontsize=8)
            for spine in ax.spines.values():
                spine.set_color("#2E3947")
            ax.tick_params(colors="#9AA5B1"); ax.grid(alpha=0.15)
            st.pyplot(fig)
        section_done_checkbox("Folgen und Reihen", "ε-N-Rechner")

    with tabs[6]:
        mini_quiz("Folgen und Reihen")

# ----------------------------------------------------------------------------
# THEMA 3: Vollständige Induktion
# ----------------------------------------------------------------------------

def seite_induktion():
    kicker("Thema 3 · Klausur-Fokus: Teilbarkeit durch 7 & Summenformeln")
    st.title("Vollständige Induktion")
    klausur_pill(True, "🔥 Teilbarkeit durch 7 (angekündigt)")
    klausur_pill(True, "🔥 Summenformel (angekündigt)")

    tabs = st.tabs(["💡 Intuition", "📖 Kochrezept", "🧠 Merkregeln",
                    "✏️ Teilbarkeit durch 7", "✏️ Summenformeln", "🎯 Quiz"])

    with tabs[0]:
        st.markdown("""
Induktion ist das **Dominoprinzip**: Wenn (1) der erste Stein fällt und (2) jeder
fallende Stein den nächsten umstößt, dann fallen *alle* Steine.

- **Induktionsanfang (IA)** = der erste Stein fällt: Aussage für $n = 1$ nachrechnen.
- **Induktionsschritt (IS)** = Stein $n$ stößt Stein $n{+}1$ um: Aus der Annahme,
  dass die Aussage für ein $n$ gilt (**IV**), folgt sie für $n{+}1$.

**Wann Induktion?** Immer wenn eine Aussage „für alle $n \\in \\mathbb{N}$“ bewiesen
werden soll — typisch: Summenformeln, Teilbarkeit, Ungleichungen.
""")
        section_done_checkbox("Vollständige Induktion", "Intuition")

    with tabs[1]:
        rezept("""
<b>1. IA (Induktionsanfang):</b> Aussage für n = 1 (oder n₀) nachrechnen — linke und
rechte Seite <b>getrennt</b> berechnen und vergleichen.<br>
<b>2. IV (Induktionsvoraussetzung):</b> „Die Aussage gelte für ein beliebiges, festes n ∈ ℕ.“
Wörtlich hinschreiben!<br>
<b>3. IS (Induktionsschritt n → n+1):</b> Behauptung für n+1 hinschreiben, dann die linke
Seite so <b>umformen, dass die IV einsetzbar</b> wird, IV einsetzen, Rest zur rechten
Seite umformen.<br>
<b>4. Schlusssatz:</b> „Nach dem Prinzip der vollständigen Induktion gilt die Aussage
für alle n ∈ ℕ.“ ∎""")
        st.markdown("**Die zwei angekündigten Grundmuster:**")
        musterbox("""
<b>Wenn</b> Summe $\\sum_{k=1}^{n+1}$ <b>dann</b> letzten Summanden abspalten:
$\\sum_{k=1}^{n+1} = \\sum_{k=1}^{n} + (\\text{Glied } n{+}1)$ → IV auf die Summe anwenden.<br><br>
<b>Wenn</b> Teilbarkeit von $c^{n+1} \\pm \\dots$ <b>dann</b> so aufspalten, dass der
IV-Term als Faktor auftaucht: $c^{n+1} = c \\cdot c^n$, dann geschickt <b>±-Nullergänzung</b>.""")
        section_done_checkbox("Vollständige Induktion", "Kochrezept")

    with tabs[2]:
        merkkasten("""
• IV heißt <b>„für EIN festes n“</b> — nicht „für alle n“ (das wäre zirkulär!).<br>
• Im IS gilt: <b>Ziel hinschreiben</b> (was für n+1 rauskommen soll), dann darauf hinarbeiten.<br>
• Teilbarkeit formal: $7 \\mid x$ heißt $x = 7m$ für ein $m \\in \\mathbb{Z}$.<br>
• Nullergänzung ist DER Trick: $8 \\cdot 8^n - 1 = 8 \\cdot 8^n \\mathbf{- 8 + 8} - 1$.""")
        warnbox("""
1. IA vergessen oder nur „stimmt offensichtlich“ schreiben — <b>immer nachrechnen</b>.<br>
2. Im IS die Behauptung für n+1 <b>verwenden statt zeigen</b> (Zirkelschluss).<br>
3. Bei Summen das neue Glied falsch bilden: bei $\\sum k^2$ ist das neue Glied $(n{+}1)^2$, nicht $n^2{+}1$.<br>
4. Schlusssatz vergessen — kostet in der Klausur oft einen Punkt.""")
        section_done_checkbox("Vollständige Induktion", "Merkregeln")

    with tabs[3]:
        aufgabe("I1", "Zeige mit vollständiger Induktion: $7 \\mid 8^n - 1$ für alle $n \\in \\mathbb{N}$.", None, [
            ("**IA** ($n=1$): $8^1 - 1 = 7 = 7 \\cdot 1$ ✓ — durch 7 teilbar.", None),
            ("**IV:** Es gelte $7 \\mid 8^n - 1$ für ein festes $n \\in \\mathbb{N}$, "
             "d. h. $8^n - 1 = 7m$ für ein $m \\in \\mathbb{Z}$.", None),
            ("**IS** ($n \\to n+1$): Zu zeigen: $7 \\mid 8^{n+1} - 1$. Umformen mit Nullergänzung:",
             r"8^{n+1} - 1 = 8 \cdot 8^n - 8 + 7 = 8\,(8^n - 1) + 7"),
            ("IV einsetzen:", r"= 8 \cdot 7m + 7 = 7\,(8m + 1)"),
            ("Das ist ein Vielfaches von 7. ✓", None),
            ("**Schlusssatz:** Nach dem Prinzip der vollständigen Induktion gilt "
             "$7 \\mid 8^n - 1$ für alle $n \\in \\mathbb{N}$. ∎", None),
        ], "●●○")
        aufgabe("I2", "Zeige: $7 \\mid 3^{2n} - 2^n$ für alle $n \\in \\mathbb{N}$.", None, [
            ("Vorüberlegung: $3^{2n} = 9^n$ — das macht die Struktur sichtbar.", None),
            ("**IA** ($n=1$): $9 - 2 = 7$ ✓.", None),
            ("**IV:** $9^n - 2^n = 7m$ für ein festes $n$.", None),
            ("**IS:** Nullergänzung so wählen, dass $9^n - 2^n$ entsteht:",
             r"9^{n+1} - 2^{n+1} = 9 \cdot 9^n - 2 \cdot 2^n = 9\,(9^n - 2^n) + 9 \cdot 2^n - 2 \cdot 2^n"),
            ("Zusammenfassen:", r"= 9\,(9^n - 2^n) + 7 \cdot 2^n = 9 \cdot 7m + 7 \cdot 2^n = 7\,(9m + 2^n)"),
            ("⟹ durch 7 teilbar. ∎", None),
        ], "●●●")
        section_done_checkbox("Vollständige Induktion", "Teilbarkeit")

    with tabs[4]:
        aufgabe("I3", "Zeige: $\\displaystyle\\sum_{k=1}^{n} k = \\frac{n(n+1)}{2}$ für alle $n \\in \\mathbb{N}$.", None, [
            ("**IA** ($n=1$): links $1$, rechts $\\frac{1 \\cdot 2}{2} = 1$ ✓.", None),
            ("**IV:** $\\sum_{k=1}^{n} k = \\frac{n(n+1)}{2}$ für ein festes $n$.", None),
            ("**IS:** Letzten Summanden abspalten und IV einsetzen:",
             r"\sum_{k=1}^{n+1} k = \underbrace{\sum_{k=1}^{n} k}_{\text{IV}} + (n+1) = \frac{n(n+1)}{2} + (n+1)"),
            ("Auf einen Bruch bringen und $(n+1)$ ausklammern:",
             r"= \frac{n(n+1) + 2(n+1)}{2} = \frac{(n+1)(n+2)}{2}"),
            ("Das ist genau die Formel mit $n+1$ statt $n$. ∎", None),
        ], "●●○")
        aufgabe("I4", "Zeige: $\\displaystyle\\sum_{k=1}^{n} (2k-1) = n^2$ (Summe der ersten $n$ ungeraden Zahlen).", None, [
            ("**IA** ($n=1$): links $1$, rechts $1^2 = 1$ ✓.", None),
            ("**IV:** $\\sum_{k=1}^{n} (2k-1) = n^2$ für ein festes $n$.", None),
            ("**IS:** Neues Glied für $k = n+1$ ist $2(n+1) - 1 = 2n + 1$:",
             r"\sum_{k=1}^{n+1} (2k-1) = n^2 + (2n+1) = (n+1)^2"),
            ("(1. binomische Formel rückwärts.) ∎", None),
        ], "●●○")
        section_done_checkbox("Vollständige Induktion", "Summenformeln")

    with tabs[5]:
        mini_quiz("Vollständige Induktion")

# ----------------------------------------------------------------------------
# THEMA 4: Differentialrechnung
# ----------------------------------------------------------------------------

def seite_diff():
    kicker("Thema 4 · Klausur-Fokus: Symmetrie, sin/cos, Sattel-/Extrempunkte")
    st.title("Differentialrechnung & Kurvendiskussion")
    klausur_pill(True, "🔥 Symmetrie sin/cos")
    klausur_pill(True, "🔥 Sattelpunkt / Extrempunkt / Minimum")

    tabs = st.tabs(["💡 Intuition", "📖 Regeln", "📈 Kurvendiskussion",
                    "🧠 Merkregeln", "✏️ Klausuraufgaben", "🎯 Quiz"])

    with tabs[0]:
        st.markdown("""
Die Ableitung $f'(x_0)$ ist die **momentane Steigung** — die Steigung der Tangente.
Alles in der Kurvendiskussion folgt aus dieser einen Idee:

- $f' > 0$: es geht bergauf (monoton wachsend), $f' < 0$: bergab
- $f' = 0$: horizontale Tangente — **Kandidat** für Max/Min/Sattelpunkt
- $f''$ misst, wie sich die Steigung ändert: $f'' > 0$ Linkskurve (konvex, „Tal“),
  $f'' < 0$ Rechtskurve („Berg“)
""")
        st.pyplot(plot_sin_cos())
        st.markdown("""
**Symmetrie an sin/cos ablesen:** $\\sin(-x) = -\\sin(x)$ (ungerade ⟹ punktsymmetrisch
zum Ursprung), $\\cos(-x) = \\cos(x)$ (gerade ⟹ achsensymmetrisch zur y-Achse).
""")
        section_done_checkbox("Differentialrechnung", "Intuition")

    with tabs[1]:
        st.markdown("**Ableitungsregeln:**")
        st.latex(r"(u \pm v)' = u' \pm v', \qquad (c \cdot u)' = c \cdot u'")
        st.latex(r"\text{Produkt: } (uv)' = u'v + uv' \qquad \text{Quotient: } \left(\frac{u}{v}\right)' = \frac{u'v - uv'}{v^2}")
        st.latex(r"\text{Kette: } \big(f(g(x))\big)' = f'(g(x)) \cdot g'(x) \quad \text{(äußere mal innere)}")
        st.markdown("**Wichtige Ableitungen:**")
        st.latex(r"(x^n)' = n x^{n-1},\quad (e^x)' = e^x,\quad (\ln x)' = \tfrac{1}{x},\quad (\sin x)' = \cos x,\quad (\cos x)' = -\sin x")
        section_done_checkbox("Differentialrechnung", "Regeln")

    with tabs[2]:
        rezept("""
<b>Kurvendiskussion — vollständiges Rezept:</b><br>
1. Definitionsbereich<br>
2. <b>Symmetrie</b>: f(−x) berechnen. = f(x) ⟹ gerade/achsensym.; = −f(x) ⟹ ungerade/punktsym.<br>
3. Nullstellen: f(x) = 0<br>
4. f′, f″ (ggf. f‴) berechnen<br>
5. <b>Kandidaten</b>: f′(x₀) = 0 lösen<br>
6. <b>Einordnen</b>: f″(x₀) &lt; 0 ⟹ Maximum · f″(x₀) &gt; 0 ⟹ Minimum ·
f″(x₀) = 0 und f‴(x₀) ≠ 0 ⟹ <b>Sattelpunkt</b><br>
7. Wendepunkte: f″ = 0 mit Vorzeichenwechsel<br>
8. Verhalten für x → ±∞, Skizze""")
        musterbox("""
<b>Wenn</b> f″(x₀) = 0 <b>dann</b> ist NICHTS entschieden — weiter mit f‴ oder
Vorzeichenwechsel von f′ prüfen!<br>
<b>Wenn</b> nur gerade Potenzen (+ cos) <b>dann</b> gerade Funktion.<br>
<b>Wenn</b> nur ungerade Potenzen (+ sin) <b>dann</b> ungerade Funktion.<br>
<b>Wenn</b> gemischt <b>dann</b> i. d. R. keine Symmetrie.""")
        section_done_checkbox("Differentialrechnung", "Kurvendiskussion")

    with tabs[3]:
        merkkasten("""
• Sattelpunkt = horizontale Tangente <b>ohne</b> Extremum: f′ = 0, f″ = 0, f‴ ≠ 0
(Paradebeispiel: x³ bei 0).<br>
• Extremum-Check-Alternative: <b>Vorzeichenwechsel von f′</b> (+→− Max, −→+ Min) —
funktioniert immer, auch wenn f″ = 0.<br>
• gerade × gerade = gerade · ungerade × ungerade = gerade · gerade × ungerade = ungerade
(wie Vorzeichenregeln).""")
        warnbox("""
1. Kettenregel vergessen: $(\\sin(2x))' = 2\\cos(2x)$, nicht $\\cos(2x)$.<br>
2. Aus f″(x₀) = 0 „Wendepunkt“ folgern <b>ohne Vorzeichenwechsel zu prüfen</b>.<br>
3. f′(x₀) = 0 sofort „Extremum“ nennen — es kann ein Sattelpunkt sein!""")
        section_done_checkbox("Differentialrechnung", "Merkregeln")

    with tabs[4]:
        aufgabe("D1", "Diskutiere $f(x) = x^3 - 3x$: Symmetrie, Extrempunkte, Wendepunkt.", None, [
            ("**Symmetrie:** $f(-x) = -x^3 + 3x = -(x^3 - 3x) = -f(x)$ "
             "⟹ ungerade, punktsymmetrisch zum Ursprung.", None),
            ("Ableitungen:", r"f'(x) = 3x^2 - 3, \qquad f''(x) = 6x, \qquad f'''(x) = 6"),
            ("Kandidaten: $3x^2 - 3 = 0 \\iff x = \\pm 1$.", None),
            ("Einordnen: $f''(-1) = -6 < 0$ ⟹ **Maximum** bei $(-1,\\ f(-1)) = (-1,\\ 2)$; "
             "$f''(1) = 6 > 0$ ⟹ **Minimum** bei $(1,\\ -2)$.", None),
            ("Wendepunkt: $f''(x) = 6x = 0 \\iff x = 0$, Vorzeichenwechsel von $-$ nach $+$ ✓ "
             "⟹ Wendepunkt $(0, 0)$.", None),
        ], "●●○")
        aufgabe("D2", "Zeige, dass $f(x) = x^3$ bei $x = 0$ einen **Sattelpunkt** hat.", None, [
            ("Ableitungen: $f' = 3x^2$, $f'' = 6x$, $f''' = 6$.", None),
            ("$f'(0) = 0$ (horizontale Tangente), $f''(0) = 0$ (kein Krümmungsentscheid).", None),
            ("$f'''(0) = 6 \\ne 0$ ⟹ Wendepunkt mit horizontaler Tangente = **Sattelpunkt**.", None),
            ("Alternative Begründung: $f'(x) = 3x^2 \\ge 0$ ohne Vorzeichenwechsel "
             "⟹ kein Extremum trotz $f'(0)=0$.", None),
        ], "●●○")
        aufgabe("D3", "Leite ab: $g(x) = e^{x} \\sin(2x)$.", None, [
            ("Produktregel mit $u = e^x$, $v = \\sin(2x)$; bei $v$ Kettenregel:", None),
            ("", r"g'(x) = e^x \sin(2x) + e^x \cdot 2\cos(2x) = e^x\big(\sin(2x) + 2\cos(2x)\big)"),
        ], "●●○")
        section_done_checkbox("Differentialrechnung", "Klausuraufgaben")

    with tabs[5]:
        mini_quiz("Differentialrechnung")

# ----------------------------------------------------------------------------
# THEMA 5: Integralrechnung  (höchster Klausur-Fokus)
# ----------------------------------------------------------------------------

def seite_integral():
    kicker("Thema 5 · HÖCHSTER Klausur-Fokus: Substitution, part. Integration, PBZ, sin-im-Zähler")
    st.title("Integralrechnung")
    klausur_pill(True, "🔥 Substitution")
    klausur_pill(True, "🔥 Partielle Integration")
    klausur_pill(True, "🔥 Partialbruchzerlegung")
    klausur_pill(True, "🔥 sin im Zähler / Funktion im Nenner (angekündigt!)")

    tabs = st.tabs(["💡 Intuition", "🔍 Verfahren erkennen", "① Substitution",
                    "② Partielle Integration", "③ Partialbruchzerlegung",
                    "⭐ sin-im-Zähler-Typ", "🧠 Merk & Fehler", "🎯 Quiz"])

    with tabs[0]:
        st.markdown("""
Integrieren ist **Rückwärts-Ableiten**. Die drei Verfahren sind Rückwärts-Versionen
der Ableitungsregeln:

| Ableitungsregel | Rückwärts = Integrationsverfahren |
|---|---|
| Kettenregel | **Substitution** |
| Produktregel | **Partielle Integration** |
| — (Algebra-Trick) | **Partialbruchzerlegung** (Bruch erst zerlegen, dann elementar integrieren) |

Der ganze Klausurerfolg hängt an einer Fähigkeit: **in 5 Sekunden erkennen, welches
Verfahren passt.** Genau dafür ist der nächste Tab da.
""")
        section_done_checkbox("Integralrechnung", "Intuition")

    with tabs[1]:
        musterbox("""
<b>Wenn</b> im Integranden „<i>innere Funktion × ihre Ableitung</i>“ steckt
(z. B. $2x \\cdot e^{x^2}$) <b>dann</b> Substitution u = innere Funktion.<br><br>
<b>Wenn</b> der Zähler die <b>Ableitung des Nenners</b> ist (ggf. bis auf Konstante)
<b>dann</b> sofort: $\\int \\frac{f'}{f} = \\ln|f| + C$. ← <i>Das ist der sin-im-Zähler-Typ!</i><br><br>
<b>Wenn</b> Produkt zweier „unverwandter“ Funktionen (Polynom × e-Funktion,
Polynom × sin/cos, ln × irgendwas) <b>dann</b> partielle Integration (LIATE).<br><br>
<b>Wenn</b> gebrochen-rational (Polynom durch Polynom) und der Nenner faktorisierbar
<b>dann</b> Partialbruchzerlegung. (Zählergrad ≥ Nennergrad? Erst Polynomdivision!)<br><br>
<b>Wenn</b> nichts davon <b>dann</b> vereinfachen (ausmultiplizieren, Bruch aufteilen,
trigonometrische Identität) und neu schauen.""",
        "Der 5-Sekunden-Entscheidungsbaum")
        section_done_checkbox("Integralrechnung", "Verfahren erkennen")

    with tabs[2]:
        rezept("""
<b>Substitution — Kochrezept:</b><br>
1. Innere Funktion wählen: u = g(x) (das, dessen Ableitung woanders im Integral steht)<br>
2. du = g′(x) dx bilden und nach dx auflösen<br>
3. <b>Alles</b> ersetzen — es darf kein x mehr übrig bleiben!<br>
4. In u integrieren<br>
5. <b>Rücksubstituieren</b> u = g(x)<br>
6. Kontrolle: Ergebnis ableiten ⟹ Integrand?""")
        aufgabe("S1", "Berechne:", r"\int 2x\, e^{x^2}\, dx", [
            ("**Erkennen:** $x^2$ innen, seine Ableitung $2x$ steht davor ⟹ Substitution.", None),
            ("Setze $u = x^2$ ⟹ $du = 2x\\,dx$.", None),
            ("Ersetzen:", r"\int e^u\, du = e^u + C"),
            ("Rücksubstitution:", r"= e^{x^2} + C"),
            ("Kontrolle: $(e^{x^2})' = 2x\\,e^{x^2}$ ✓ (Kettenregel).", None),
        ], "●○○")
        aufgabe("S2", "Berechne:", r"\int \frac{x}{x^2 + 1}\, dx", [
            ("**Erkennen:** Ableitung des Nenners ist $2x$ — der Zähler $x$ ist die Hälfte davon "
             "⟹ ln-Typ mit Faktor $\\tfrac12$.", None),
            ("$u = x^2 + 1$, $du = 2x\\,dx$ ⟹ $x\\,dx = \\tfrac12 du$:",
             r"\int \frac{1}{u} \cdot \frac{1}{2}\,du = \frac{1}{2}\ln|u| + C = \frac{1}{2}\ln(x^2+1) + C"),
            ("(Betrag entfällt: $x^2 + 1 > 0$.)", None),
        ], "●●○")
        section_done_checkbox("Integralrechnung", "Substitution")

    with tabs[3]:
        rezept("""
<b>Partielle Integration:</b> $\\int u\\,v'\\,dx = u\\,v - \\int u'\\,v\\,dx$<br><br>
<b>Wahl von u nach LIATE</b> (was zuerst in der Liste steht, wird u — weil es beim
Ableiten „einfacher“ wird):<br>
<b>L</b>ogarithmus → <b>I</b>nverse (arctan …) → <b>A</b>lgebraisch (x, x²) →
<b>T</b>rigonometrisch → <b>E</b>xponentiell""")
        aufgabe("P1", "Berechne:", r"\int x\, e^{x}\, dx", [
            ("**Erkennen:** Produkt aus Polynom und e-Funktion ⟹ partiell. "
             "LIATE: A vor E ⟹ $u = x$, $v' = e^x$.", None),
            ("$u' = 1$, $v = e^x$:",
             r"\int x e^x dx = x e^x - \int 1 \cdot e^x dx = x e^x - e^x + C = (x-1)e^x + C"),
            ("Kontrolle: $((x-1)e^x)' = e^x + (x-1)e^x = x e^x$ ✓.", None),
        ], "●○○")
        aufgabe("P2", "Berechne (Klassiker!):", r"\int \ln x\, dx", [
            ("**Trick:** $\\ln x = 1 \\cdot \\ln x$. LIATE: L ganz vorne ⟹ $u = \\ln x$, $v' = 1$.", None),
            ("$u' = \\tfrac{1}{x}$, $v = x$:",
             r"\int \ln x\, dx = x \ln x - \int \frac{1}{x} \cdot x\, dx = x\ln x - x + C"),
        ], "●●○")
        aufgabe("P3", "Berechne:", r"\int x \cos x \, dx", [
            ("LIATE: A vor T ⟹ $u = x$, $v' = \\cos x$, also $u' = 1$, $v = \\sin x$:",
             r"\int x\cos x\,dx = x \sin x - \int \sin x \, dx = x\sin x + \cos x + C"),
            ("Kontrolle durch Ableiten: $\\sin x + x\\cos x - \\sin x = x\\cos x$ ✓.", None),
        ], "●●○")
        section_done_checkbox("Integralrechnung", "Partielle Integration")

    with tabs[4]:
        rezept("""
<b>Partialbruchzerlegung — Kochrezept:</b><br>
0. Zählergrad ≥ Nennergrad? ⟹ zuerst <b>Polynomdivision</b><br>
1. Nenner vollständig <b>faktorisieren</b> (Nullstellen bestimmen)<br>
2. <b>Ansatz</b>:<br>
&nbsp;&nbsp;• einfache Nullstelle a: $\\frac{A}{x-a}$<br>
&nbsp;&nbsp;• doppelte Nullstelle a: $\\frac{A}{x-a} + \\frac{B}{(x-a)^2}$<br>
&nbsp;&nbsp;• irreduzibel quadratisch: $\\frac{Ax+B}{x^2+px+q}$<br>
3. Mit dem Nenner <b>durchmultiplizieren</b><br>
4. Koeffizienten bestimmen: <b>Zuhaltemethode</b> (Nullstellen einsetzen) oder
Koeffizientenvergleich<br>
5. Jeden Partialbruch integrieren: $\\int\\frac{A}{x-a} = A\\ln|x-a|$,
$\\int\\frac{B}{(x-a)^2} = -\\frac{B}{x-a}$""")
        aufgabe("B1", "Berechne:", r"\int \frac{5x + 1}{(x-1)(x+2)}\, dx", [
            ("**Erkennen:** gebrochen-rational, Nenner schon faktorisiert, Zählergrad 1 < Nennergrad 2 "
             "⟹ direkt PBZ.", None),
            ("Ansatz:", r"\frac{5x+1}{(x-1)(x+2)} = \frac{A}{x-1} + \frac{B}{x+2}"),
            ("Durchmultiplizieren:", r"5x + 1 = A(x+2) + B(x-1)"),
            ("**Zuhaltemethode:** $x = 1$: $6 = 3A \\Rightarrow A = 2$. "
             "$x = -2$: $-9 = -3B \\Rightarrow B = 3$.", None),
            ("Integrieren:",
             r"\int \frac{2}{x-1} + \frac{3}{x+2}\, dx = 2\ln|x-1| + 3\ln|x+2| + C"),
        ], "●●○")
        aufgabe("B2", "Berechne (doppelte Nullstelle):", r"\int \frac{x + 3}{(x-1)^2}\, dx", [
            ("Ansatz für doppelte Nullstelle:",
             r"\frac{x+3}{(x-1)^2} = \frac{A}{x-1} + \frac{B}{(x-1)^2}"),
            ("Durchmultiplizieren: $x + 3 = A(x-1) + B$.", None),
            ("$x = 1$: $4 = B$. Koeffizientenvergleich bei $x$: $1 = A$.", None),
            ("Integrieren:",
             r"\int \frac{1}{x-1}\,dx + \int \frac{4}{(x-1)^2}\,dx = \ln|x-1| - \frac{4}{x-1} + C"),
            ("⚠️ Der zweite Term ist ein **Potenz-Integral** ($u^{-2}$), KEIN ln!", None),
        ], "●●●")
        aufgabe("B3", "Berechne (erst Polynomdivision):", r"\int \frac{x^2 + 1}{x - 1}\, dx", [
            ("Zählergrad 2 ≥ Nennergrad 1 ⟹ Polynomdivision:",
             r"(x^2 + 1) : (x - 1) = x + 1 + \frac{2}{x-1}"),
            ("Jetzt gliedweise integrieren:",
             r"\int \left(x + 1 + \frac{2}{x-1}\right) dx = \frac{x^2}{2} + x + 2\ln|x-1| + C"),
        ], "●●●")
        section_done_checkbox("Integralrechnung", "Partialbruchzerlegung")

    with tabs[5]:
        st.markdown("### ⭐ Der angekündigte Typ: Sinus im Zähler, Funktion im Nenner")
        merkkasten("""
Der Dozent meint die Familie $\\int \\frac{\\sin x}{g(\\cos x)}\\,dx$.
Der Schlüssel: $(\\cos x)' = -\\sin x$ — der Zähler ist (bis aufs Vorzeichen)
die <b>innere Ableitung des Nenners</b>. Substitution $u = \\cos x$ räumt alles weg.<br><br>
Spezialfall Nenner linear in cos: $\\int \\frac{\\sin x}{\\cos x + a}\\,dx
= -\\ln|\\cos x + a| + C$ — der <b>ln-Typ</b> $\\int \\frac{f'}{f} = \\ln|f|$.""",
        "Das Muster")
        aufgabe("Z1", "Berechne:", r"\int \frac{\sin x}{\cos x + 2}\, dx", [
            ("**Erkennen:** Nenner enthält $\\cos x$, Zähler ist $\\sin x$ "
             "⟹ Zähler = −(Ableitung des Nenners) ⟹ ln-Typ.", None),
            ("Substitution $u = \\cos x + 2$ ⟹ $du = -\\sin x\\, dx$ ⟹ $\\sin x\\,dx = -du$:",
             r"\int \frac{-du}{u} = -\ln|u| + C"),
            ("Rücksubstitution (Betrag entfällt, da $\\cos x + 2 \\ge 1 > 0$):",
             r"= -\ln(\cos x + 2) + C"),
            ("Kontrolle: $\\big(-\\ln(\\cos x + 2)\\big)' = -\\frac{-\\sin x}{\\cos x + 2} "
             "= \\frac{\\sin x}{\\cos x + 2}$ ✓", None),
        ], "●●○")
        aufgabe("Z2", "Berechne:", r"\int \frac{\sin x}{\cos^2 x}\, dx", [
            ("Gleiches Muster, aber Nenner quadratisch ⟹ Potenzregel statt ln!", None),
            ("$u = \\cos x$, $du = -\\sin x\\,dx$:",
             r"\int \frac{-du}{u^2} = \frac{1}{u} + C = \frac{1}{\cos x} + C"),
            ("⚠️ Häufigster Fehler hier: reflexartig ln schreiben. "
             "ln nur bei Nenner in **erster** Potenz!", None),
        ], "●●●")
        aufgabe("Z3", "Berechne:", r"\int \tan x \, dx", [
            ("$\\tan x = \\frac{\\sin x}{\\cos x}$ — derselbe Typ in Verkleidung!", None),
            ("$u = \\cos x$:",
             r"\int \frac{\sin x}{\cos x}dx = -\ln|\cos x| + C"),
        ], "●●○")
        section_done_checkbox("Integralrechnung", "sin-im-Zähler")

    with tabs[6]:
        merkkasten("""
• $\\int \\frac{f'(x)}{f(x)}dx = \\ln|f(x)| + C$ — der wichtigste Reflex der Klausur.<br>
• Nach Substitution darf <b>kein x mehr im Integral stehen</b>.<br>
• Partiell: wird das neue Integral <b>komplizierter</b>, war die u-Wahl falsch — tauschen!<br>
• +C nie vergessen (bei unbestimmten Integralen).<br>
• Immer 10 Sekunden für die <b>Ableitungs-Kontrolle</b> investieren.""")
        warnbox("""
1. <b>Vorzeichen bei $u = \\cos x$</b>: $du = -\\sin x\\,dx$ — das Minus wandert ins Integral!<br>
2. Bei PBZ mit doppelter Nullstelle den $\\frac{B}{(x-a)^2}$-Term vergessen.<br>
3. Polynomdivision überspringen, wenn Zählergrad ≥ Nennergrad.<br>
4. $\\int \\frac{1}{u^2}du = \\ln$ … NEIN: $= -\\frac{1}{u}$ (Potenzregel!).<br>
5. Grenzen bei bestimmten Integralen nach Substitution nicht mitsubstituieren.""")
        section_done_checkbox("Integralrechnung", "Merk & Fehler")

    with tabs[7]:
        mini_quiz("Integralrechnung")

# ----------------------------------------------------------------------------
# THEMA 6: Differentialgleichungen
# ----------------------------------------------------------------------------

def seite_dgl():
    kicker("Thema 6 · Klausur-Gewicht: gering (laut Dozent) — Grundrezept reicht")
    st.title("Differentialgleichungen 1. Ordnung")
    klausur_pill(False, "Trennung der Variablen")
    klausur_pill(False, "geringes Gewicht — nicht überinvestieren")

    tabs = st.tabs(["💡 Intuition", "📖 Kochrezept", "✏️ Klausuraufgaben", "🎯 Quiz"])

    with tabs[0]:
        st.markdown("""
Eine DGL beschreibt eine Funktion **über ihre Änderungsrate**: $y' = f(x, y)$ sagt
„an jeder Stelle kenne ich die Steigung“. Lösen heißt: die Funktion rekonstruieren.

Paradebeispiel $y' = ky$: „Die Änderung ist proportional zum Bestand“ —
Wachstum/Zerfall ⟹ $y = Ce^{kx}$. Das **Anfangswertproblem** (AWP) legt mit
$y(x_0) = y_0$ die freie Konstante $C$ fest.
""")
        section_done_checkbox("Differentialgleichungen", "Intuition")

    with tabs[1]:
        rezept("""
<b>Trennung der Variablen</b> (für y′ = g(x) · h(y)):<br>
1. $\\frac{dy}{dx} = g(x)h(y)$ schreiben<br>
2. Alle y nach links, alle x nach rechts: $\\frac{dy}{h(y)} = g(x)\\,dx$<br>
3. Beide Seiten integrieren (nur EINE Konstante c nötig)<br>
4. Nach y auflösen<br>
5. AWP: Anfangswert einsetzen ⟹ C bestimmen<br>
6. Kontrolle: Lösung ableiten und in die DGL einsetzen""")
        musterbox("""
<b>Wenn</b> sich y′ = … als Produkt g(x)·h(y) schreiben lässt <b>dann</b> Trennung der Variablen.<br>
<b>Wenn</b> y′ + p(x)·y = q(x) (linear) <b>dann</b> erst homogen lösen, dann Variation der Konstanten.""")
        section_done_checkbox("Differentialgleichungen", "Kochrezept")

    with tabs[2]:
        aufgabe("G1", "Löse das AWP $y' = 2y$, $y(0) = 3$.", None, [
            ("Trennen:", r"\frac{dy}{y} = 2\,dx"),
            ("Integrieren:", r"\ln|y| = 2x + c \;\Longrightarrow\; y = C e^{2x}"),
            ("AWP: $y(0) = C = 3$ ⟹ $y(x) = 3e^{2x}$.", None),
            ("Kontrolle: $y' = 6e^{2x} = 2 \\cdot 3e^{2x} = 2y$ ✓, $y(0) = 3$ ✓.", None),
        ], "●○○")
        aufgabe("G2", "Löse $y' = x \\cdot y$ (allgemeine Lösung).", None, [
            ("Trennen:", r"\frac{dy}{y} = x\,dx"),
            ("Integrieren:", r"\ln|y| = \frac{x^2}{2} + c \;\Longrightarrow\; y = C e^{x^2/2}"),
        ], "●●○")
        aufgabe("G3", "Löse die lineare DGL $y' + y = e^{x}$.", None, [
            ("Homogene Lösung ($y' + y = 0$): $y_h = Ce^{-x}$.", None),
            ("Partikuläre Lösung: Ansatz $y_p = Ae^{x}$ (rechte Seite ist e-Funktion): "
             "$Ae^x + Ae^x = e^x \\Rightarrow A = \\tfrac12$.", None),
            ("Gesamtlösung:", r"y = C e^{-x} + \tfrac{1}{2}e^{x}"),
        ], "●●●")
        section_done_checkbox("Differentialgleichungen", "Klausuraufgaben")

    with tabs[3]:
        mini_quiz("Differentialgleichungen")

# ----------------------------------------------------------------------------
# Adaptives Quiz (themenübergreifend)
# ----------------------------------------------------------------------------

def seite_quiz():
    kicker("Trainieren · adaptiv gewichtet nach deinen Schwächen × Klausurgewicht")
    st.title("🎯 Adaptives Quiz")
    st.caption("Die App wählt Themen häufiger aus, in denen du Fehler machst — "
               "und gewichtet zusätzlich nach Klausurrelevanz (Integration > Folgen > …).")

    c1, c2 = st.columns([2, 1])
    with c2:
        st.markdown("**Deine Bilanz:**")
        for t in TOPICS:
            s = st.session_state.quiz_stats[t]
            n = s["richtig"] + s["falsch"]
            quote = f"{s['richtig']}/{n}" if n else "—"
            st.markdown(f"<span class='pill'>{t.split()[0]}: {quote}</span>",
                        unsafe_allow_html=True)

    with c1:
        if st.session_state.quiz_task is None:
            st.session_state.quiz_task = neue_aufgabe()
            st.session_state.quiz_solved = False
        task = st.session_state.quiz_task
        st.markdown(f"<span class='pill pill-hot'>{task['topic']}</span>&nbsp;"
                    f"<span class='pill'>{task['punkte']} Punkte</span>",
                    unsafe_allow_html=True)
        eingabe = render_task_input(task, "adaptiv")
        b1, b2 = st.columns(2)
        if b1.button("Prüfen", type="primary", disabled=st.session_state.quiz_solved):
            if eingabe is None:
                st.warning("Bitte erst antworten.")
            else:
                ok = check_task(task, eingabe)
                record_quiz(task["topic"], ok, task["frage_md"][:60])
                st.session_state.quiz_solved = True
                st.session_state.quiz_ok = ok
        if st.session_state.quiz_solved:
            if st.session_state.get("quiz_ok"):
                st.success("✅ Richtig!")
            else:
                st.error("❌ Falsch — Lösung ansehen und ins Fehlerheft schauen.")
            st.markdown("**Musterlösung:** " + task["loesung_md"])
            if task.get("loesung_latex"):
                st.latex(task["loesung_latex"])
        if b2.button("Nächste Aufgabe →"):
            st.session_state.quiz_task = neue_aufgabe()
            st.session_state.quiz_solved = False
            st.rerun()

# ----------------------------------------------------------------------------
# Prüfungsmodus (zufällige 90-Minuten-Klausur)
# ----------------------------------------------------------------------------

EXAM_BLUEPRINT = [
    ("Folgen und Reihen", gen_folgen_epsilon),
    ("Folgen und Reihen", gen_folgen_grenzwert),
    ("Vollständige Induktion", gen_induktion_mc),
    ("Komplexe Zahlen", gen_komplex_menge),
    ("Komplexe Zahlen", gen_komplex_betrag),
    ("Integralrechnung", gen_integration_sinus),
    ("Integralrechnung", gen_integration_pbz),
    ("Differentialrechnung", gen_ableitung),
    ("Differentialgleichungen", gen_dgl_mc),
]

def note_aus_prozent(p: float) -> str:
    grenzen = [(0.95, "1,0"), (0.90, "1,3"), (0.85, "1,7"), (0.80, "2,0"),
               (0.75, "2,3"), (0.70, "2,7"), (0.65, "3,0"), (0.60, "3,3"),
               (0.55, "3,7"), (0.50, "4,0")]
    for g, n in grenzen:
        if p >= g:
            return n
    return "5,0"

def seite_pruefung():
    kicker("Generalprobe · zufällig generierte Klausur · 90 Minuten")
    st.title("📝 Prüfungsmodus")

    if st.session_state.exam is None:
        st.markdown("""
Simuliere eine Klausur unter Echtzeit-Bedingungen: **9 Aufgaben**, gewichtet wie die
angekündigten Schwerpunkte, **90 Minuten**, automatische Bewertung mit Musterlösungen.

**Empfehlung:** Handy weg, Papier + Stift daneben, erst rechnen, dann eintragen —
genau wie in der echten Klausur.
""")
        if st.button("🚀 Klausur starten", type="primary"):
            rng = random.Random()
            tasks = [gen(rng) for _, gen in EXAM_BLUEPRINT]
            for t in tasks:
                if t["typ"] == "mc":
                    rng.shuffle(t["optionen"])
            st.session_state.exam = {
                "tasks": tasks, "start": time.time(),
                "abgegeben": False, "antworten": {},
            }
            st.rerun()
        return

    exam = st.session_state.exam
    verbleibend = 90 * 60 - (time.time() - exam["start"])

    if not exam["abgegeben"]:
        mm, ss = divmod(max(0, int(verbleibend)), 60)
        farbe = "🟢" if verbleibend > 1800 else ("🟡" if verbleibend > 600 else "🔴")
        st.markdown(f"### {farbe} Verbleibende Zeit: {mm:02d}:{ss:02d}")
        if verbleibend <= 0:
            st.error("⏰ Zeit abgelaufen — die Klausur wird gewertet.")
            exam["abgegeben"] = True
            st.rerun()
        st.caption("(Uhr aktualisiert sich bei jeder Interaktion — für echten Countdown "
                   "einen Timer daneben stellen.)")

        gesamt = sum(t["punkte"] for t in exam["tasks"])
        for i, t in enumerate(exam["tasks"]):
            with st.container(border=True):
                st.markdown(f"**Aufgabe {i+1}** · {t['topic']} · {t['punkte']}/{gesamt} P.")
                exam["antworten"][i] = render_task_input(t, f"exam_{i}")
        if st.button("✅ Abgeben und bewerten", type="primary"):
            exam["abgegeben"] = True
            exam["dauer"] = time.time() - exam["start"]
            st.rerun()
    else:
        punkte, gesamt = 0, sum(t["punkte"] for t in exam["tasks"])
        st.markdown("## Auswertung")
        for i, t in enumerate(exam["tasks"]):
            eingabe = exam["antworten"].get(i)
            ok = check_task(t, eingabe)
            if ok:
                punkte += t["punkte"]
            record_quiz(t["topic"], ok, f"Prüfungsmodus: {t['frage_md'][:50]}")
            with st.expander(f"{'✅' if ok else '❌'} Aufgabe {i+1} · {t['topic']} · "
                             f"{t['punkte'] if ok else 0}/{t['punkte']} P."):
                st.markdown(t["frage_md"])
                if t.get("latex"):
                    st.latex(t["latex"])
                st.markdown("**Musterlösung:** " + t["loesung_md"])
                if t.get("loesung_latex"):
                    st.latex(t["loesung_latex"])
        p = punkte / gesamt
        dauer_min = exam.get("dauer", 0) / 60
        st.markdown("---")
        c1, c2, c3 = st.columns(3)
        c1.metric("Punkte", f"{punkte}/{gesamt}")
        c2.metric("Prozent", f"{p*100:.0f} %")
        c3.metric("Note (Richtwert)", note_aus_prozent(p))
        if dauer_min:
            st.caption(f"Bearbeitungszeit: {dauer_min:.0f} Minuten von 90.")
        st.caption("⚠️ Der Notenschlüssel ist ein Richtwert — der echte Schlüssel deiner "
                   "Klausur kann abweichen. Wichtiger als die Note: Welche Aufgabentypen "
                   "waren falsch? → Fehlerheft.")
        if p >= 0.95:
            st.success("🏆 1,0-Niveau — weiter so, Fokus auf Tempo und Sauberkeit.")
        elif p >= 0.8:
            st.info("Solide! Die falschen Typen gezielt im Themenkapitel nacharbeiten.")
        else:
            st.warning("Noch Luft — arbeite die ❌-Aufgaben im jeweiligen Kapitel nach "
                       "und starte morgen eine neue Generalprobe.")
        if st.button("🔁 Neue Klausur generieren"):
            st.session_state.exam = None
            st.rerun()

# ----------------------------------------------------------------------------
# Spickzettel, Checkliste, Strategien, Fehlerheft, Lernstand
# ----------------------------------------------------------------------------

def seite_spickzettel():
    kicker("Alles Wichtige auf einer Seite · zum Ausdrucken durchscrollen")
    st.title("📜 Formel-Spickzettel")
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("#### Komplexe Zahlen")
        st.latex(r"|z| = \sqrt{a^2+b^2}, \quad z = re^{i\varphi}, \quad z^n = r^n e^{in\varphi}")
        st.latex(r"z_k = \sqrt[n]{r}\,e^{i\frac{\varphi+2\pi k}{n}},\; k=0..n{-}1")
        st.latex(r"\frac{z}{w} = \frac{z\overline{w}}{|w|^2}")
        st.markdown("#### Folgen")
        st.latex(r"|a_n - a| < \varepsilon \ \forall n \ge N")
        st.latex(r"\tfrac1n \to 0,\; q^n \to 0\,(|q|{<}1),\; \sqrt[n]{n} \to 1,\; (1{+}\tfrac1n)^n \to e")
        st.markdown("#### Induktion")
        st.markdown("IA (n=1 nachrechnen) → IV (für ein festes n) → IS (n→n+1, IV einsetzen) → ∎")
        st.latex(r"\sum_{k=1}^n k = \frac{n(n+1)}{2}, \qquad \sum_{k=1}^n k^2 = \frac{n(n+1)(2n+1)}{6}")
    with c2:
        st.markdown("#### Ableitungen")
        st.latex(r"(uv)' = u'v + uv', \quad \left(\tfrac{u}{v}\right)' = \tfrac{u'v - uv'}{v^2}, \quad (f\circ g)' = f'(g)\,g'")
        st.latex(r"(\sin)' = \cos,\; (\cos)' = -\sin,\; (e^x)' = e^x,\; (\ln x)' = \tfrac1x")
        st.markdown("Max: f″<0 · Min: f″>0 · **Sattel: f′=0, f″=0, f‴≠0**")
        st.markdown("#### Integrale")
        st.latex(r"\int \frac{f'(x)}{f(x)}dx = \ln|f(x)| + C \quad \leftarrow \text{sin-im-Zähler-Typ!}")
        st.latex(r"\int u v' = uv - \int u'v \quad \text{(LIATE)}")
        st.latex(r"\int \frac{A}{x-a} = A\ln|x-a|, \quad \int \frac{B}{(x-a)^2} = -\frac{B}{x-a}")
        st.markdown("#### DGL")
        st.latex(r"y' = g(x)h(y) \Rightarrow \int \frac{dy}{h(y)} = \int g(x)dx")
        st.latex(r"y' = ky \Rightarrow y = Ce^{kx}")

def seite_strategie():
    kicker("Zeitmanagement, Reihenfolge, Kontrolle")
    st.title("🧭 Klausurstrategie & Checkliste")
    st.markdown("""
### Reihenfolge in der Klausur
1. **Erst die Schema-Aufgaben sichern** (5–10 Min. Puffer aufbauen): Induktion und
   die ε-Abschätzung (Aufgabe-34-Typ) sind planbar — die zuerst, sauber, mit Antwortsatz.
2. **Dann Integration** — hier liegen die meisten Punkte UND die meisten Fehlerquellen.
   Pro Integral: 5-Sekunden-Check „welches Verfahren?“, dann erst losrechnen.
3. Komplexe Mengen & Kurvendiskussion.
4. DGL zum Schluss (geringstes Gewicht).

### Zeitregeln
- **Punkte ÷ Gesamtpunkte × 90 ≈ Minuten pro Aufgabe.** Bei Überziehung: markieren, weiter.
- Letzte 10 Minuten = reine Kontrollzeit (siehe unten).

### Kontroll- & Plausibilitätsstrategien
- Jedes unbestimmte Integral: **einmal ableiten** — 15 Sekunden, rettet 5 Punkte.
- ε-Aufgabe: $a_N$ ausrechnen und prüfen, ob es wirklich im ε-Schlauch liegt.
- Komplexe Wurzeln: müssen ein regelmäßiges n-Eck bilden — Skizze als Plausibilitätscheck.
- Induktion: steht der Schlusssatz da? Ist die IV wörtlich formuliert?
- Vorzeichen-Hotspots: $du = -\\sin x\\,dx$, Quotientenregel-Zähler, $(\\cos)' = -\\sin$.

### Checkliste Abend vor der Klausur
- [ ] Aufgabe 34 einmal blind durchgerechnet
- [ ] Ein Teilbarkeits- und ein Summen-Induktionsbeweis blind
- [ ] Ein sin-im-Zähler-Integral + eine PBZ blind
- [ ] Eine komplexe Menge skizziert (Rand gestrichelt vs. durchgezogen!)
- [ ] Fehlerheft komplett durchgelesen
- [ ] Taschenrechner/Geodreieck/Stifte gepackt, früh schlafen
""")

def seite_fehlerheft():
    kicker("Dein persönliches Fehlerprotokoll — am Tag vor der Klausur nur noch DAS lesen")
    st.title("📕 Fehlerheft")
    if not st.session_state.fehlerheft:
        st.info("Noch leer — Fehler aus Quiz und Prüfungsmodus landen automatisch hier. "
                "Eigene Einträge kannst du unten ergänzen.")
    else:
        for eintrag in reversed(st.session_state.fehlerheft):
            st.markdown(f"- {eintrag}")
    neu = st.text_input("Eigenen Fehler notieren (z. B. „Vorzeichen bei du = −sin x dx vergessen“):")
    if st.button("➕ Eintragen") and neu.strip():
        st.session_state.fehlerheft.append(
            f"{datetime.now().strftime('%d.%m. %H:%M')} · Notiz: {neu.strip()}")
        st.rerun()
    if st.session_state.fehlerheft and st.button("🗑️ Fehlerheft leeren"):
        st.session_state.fehlerheft = []
        st.rerun()

def seite_lernstand():
    kicker("Fortschritt sichern & wiederherstellen")
    st.title("💾 Lernstand")
    st.markdown("Streamlit vergisst beim Schließen — **lade deinen Stand als Datei herunter** "
                "und lade ihn beim nächsten Mal wieder hoch.")
    export = {
        "done_sections": {k: sorted(v) for k, v in st.session_state.done_sections.items()},
        "quiz_stats": st.session_state.quiz_stats,
        "fehlerheft": st.session_state.fehlerheft,
        "gespeichert": datetime.now().isoformat(timespec="seconds"),
    }
    st.download_button("⬇️ Lernstand herunterladen (JSON)",
                       data=json.dumps(export, ensure_ascii=False, indent=2),
                       file_name="mathe1_lernstand.json", mime="application/json")
    up = st.file_uploader("⬆️ Lernstand hochladen", type=["json"])
    if up is not None:
        try:
            data = json.load(up)
            st.session_state.done_sections = {k: set(v) for k, v in data.get("done_sections", {}).items()}
            st.session_state.quiz_stats = data.get("quiz_stats", st.session_state.quiz_stats)
            st.session_state.fehlerheft = data.get("fehlerheft", [])
            st.success(f"Lernstand vom {data.get('gespeichert', '?')} geladen ✅")
        except Exception as ex:
            st.error(f"Datei konnte nicht gelesen werden: {ex}")

# ----------------------------------------------------------------------------
# Suche
# ----------------------------------------------------------------------------

SEARCH_INDEX = {
    "Komplexe Zahlen": ["betrag", "argument", "polarform", "exponentialform", "de moivre",
                        "wurzeln", "konjugiert", "division", "mengen", "kreis", "quadrant",
                        "i^2", "imaginär"],
    "Folgen und Reihen": ["grenzwert", "epsilon", "abschätzung", "aufgabe 34", "monotonie",
                          "beschränkt", "konvergenz", "divergenz", "folge", "n bestimmen"],
    "Vollständige Induktion": ["induktion", "teilbarkeit", "durch 7", "summenformel",
                               "induktionsanfang", "induktionsschritt", "dominoeffekt",
                               "gaußsche summenformel", "nullergänzung"],
    "Differentialrechnung": ["ableitung", "produktregel", "quotientenregel", "kettenregel",
                             "kurvendiskussion", "extrempunkt", "minimum", "maximum",
                             "sattelpunkt", "wendepunkt", "symmetrie", "sinus", "cosinus",
                             "monotonie", "krümmung"],
    "Integralrechnung": ["integral", "substitution", "partielle integration", "liate",
                         "partialbruchzerlegung", "pbz", "stammfunktion", "sinus im zähler",
                         "ln-typ", "polynomdivision", "tan", "cos im nenner"],
    "Differentialgleichungen": ["dgl", "trennung der variablen", "anfangswertproblem", "awp",
                                "variation der konstanten", "wachstum", "erster ordnung"],
}

# ----------------------------------------------------------------------------
# Sidebar & Router
# ----------------------------------------------------------------------------

PAGES = {
    "🏠 Start & Lernplan": "start",
    "1️⃣ Komplexe Zahlen": "komplex",
    "2️⃣ Folgen und Reihen": "folgen",
    "3️⃣ Vollständige Induktion": "induktion",
    "4️⃣ Differentialrechnung": "diff",
    "5️⃣ Integralrechnung": "integral",
    "6️⃣ Differentialgleichungen": "dgl",
    "🎯 Adaptives Quiz": "quiz",
    "📝 Prüfungsmodus": "pruefung",
    "📜 Spickzettel": "spick",
    "🧭 Klausurstrategie": "strategie",
    "📕 Fehlerheft": "fehler",
    "💾 Lernstand": "lernstand",
}

def seite_start():
    kicker("Mathematik 1 · THI · Ziel: 1,0")
    st.title("Dein Klausur-Coach")
    st.progress(gesamt_fortschritt(),
                text=f"Gesamtfortschritt: {gesamt_fortschritt()*100:.0f} % der Abschnitte abgehakt")
    st.markdown("""
Diese App ist nach den **Dozenten-Hinweisen** gewichtet. Empfohlene Route (7 Tage):

| Tag | Fokus | In der App |
|---|---|---|
| 1 | Folgen + ε-Abschätzung | Kapitel 2 → **Aufgabe 34** dreimal, ε-N-Rechner, Quiz |
| 2 | Induktion (÷7 & Summen) | Kapitel 3 komplett + Quiz |
| 3 | Integration I | Kapitel 5: Substitution, part. Integration, **sin-im-Zähler** |
| 4 | Integration II | Kapitel 5: PBZ (alle drei Aufgaben!) + Quiz bis 10 richtige |
| 5 | Komplex + Kurvendiskussion | Kapitel 1 (Mengen!) + Kapitel 4 |
| 6 | DGL kurz + **Generalprobe** | Kapitel 6, dann 📝 Prüfungsmodus (90 Min, ehrlich!) |
| 7 | Lücken schließen | 📕 Fehlerheft lesen, ❌-Typen nacharbeiten, 📜 Spickzettel |
""")
    st.markdown("#### Klausur-Gewichtung (aus den Vorlesungs-Hinweisen)")
    for t in sorted(TOPICS, key=lambda x: -EXAM_WEIGHT[x]):
        st.progress(EXAM_WEIGHT[t] / 3.0, text=t)

def main():
    with st.sidebar:
        st.markdown("## 📐 Mathe 1 · Coach")
        st.progress(gesamt_fortschritt())
        suche = st.text_input("🔎 Suche", placeholder="z. B. Sattelpunkt, PBZ, ε …")
        if suche:
            treffer = [t for t, kws in SEARCH_INDEX.items()
                       if any(suche.lower() in kw or kw in suche.lower() for kw in kws)
                       or suche.lower() in t.lower()]
            if treffer:
                st.caption("Gefunden in: " + " · ".join(f"**{t}**" for t in treffer))
            else:
                st.caption("Kein Treffer — probiere ein Fachwort (z. B. „Substitution“).")
        wahl = st.radio("Navigation", list(PAGES.keys()), label_visibility="collapsed")
        st.divider()
        st.toggle("🌙 Dunkles Design (Boxen)", key="dark_mode")
        st.caption("Basistheme: Menü ▸ Settings ▸ Theme")
        s_ges = st.session_state.quiz_stats
        richtig = sum(v["richtig"] for v in s_ges.values())
        falsch = sum(v["falsch"] for v in s_ges.values())
        st.caption(f"Quiz-Bilanz gesamt: ✅ {richtig} · ❌ {falsch}")

    page = PAGES[wahl]
    if page == "start":
        seite_start()
    elif page == "komplex":
        seite_komplex()
    elif page == "folgen":
        seite_folgen()
    elif page == "induktion":
        seite_induktion()
    elif page == "diff":
        seite_diff()
    elif page == "integral":
        seite_integral()
    elif page == "dgl":
        seite_dgl()
    elif page == "quiz":
        seite_quiz()
    elif page == "pruefung":
        seite_pruefung()
    elif page == "spick":
        seite_spickzettel()
    elif page == "strategie":
        seite_strategie()
    elif page == "fehler":
        seite_fehlerheft()
    elif page == "lernstand":
        seite_lernstand()

main()
