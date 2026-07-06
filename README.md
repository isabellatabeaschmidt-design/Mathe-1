# Mathe 1 · Klausur-Coach (Streamlit)

Interaktive Lernplattform für die Mathematik-1-Klausur (THI), gewichtet nach den
Dozenten-Hinweisen: Integration > Folgen/Aufgabe 34 > Induktion (÷7, Summen) >
komplexe Mengen > Kurvendiskussion > DGL.

## Start
```bash
pip install streamlit matplotlib numpy
streamlit run app.py
```

## Features
- 6 Themenkapitel mit Intuition, Theorie, Kochrezepten, Schritt-für-Schritt-Klausuraufgaben,
  Merkkästen, Warnboxen (typische Fehler) und Mustererkennung ("Wenn … dann …")
- Aufgabe 34 komplett gelöst inkl. 10-%-Variante + interaktiver ε-N-Rechner mit Plot
- Komplexe Mengen zeichnen (interaktive Plots) + Polarform-Umrechner
- Mini-Quiz pro Thema mit zufällig generierten Aufgaben und sofortigem Feedback
- Adaptives Quiz: gewichtet nach deinen Fehlerquoten × Klausurrelevanz
- Prüfungsmodus: zufällige 90-Minuten-Klausur mit automatischer Bewertung und Musterlösungen
- Fehlerheft (automatisch + eigene Notizen), Spickzettel, Klausurstrategie-Checkliste
- Lernstand als JSON exportieren/importieren, Fortschrittsbalken, Suche, Dark/Light-Boxen
