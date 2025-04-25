#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Interface locale Qt (PySide6): selection des alcools avec onglets, champ de recherche,
 grille de checkboxes, tableau de resultats
 Utilise un fichier externe recipes.json encode en UTF-8 dans le meme repertoire.
 Prise en charge des synonymes pour liqueurs et whiskys.
"""
import sys
import json
import unittest
from pathlib import Path
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QApplication, QWidget, QLineEdit, QTabWidget, QCheckBox, QScrollArea,
    QGridLayout, QPushButton, QTableWidget, QTableWidgetItem, QVBoxLayout,
    QHBoxLayout, QMessageBox, QHeaderView
)

# Categories fixe des alcools
CATEGORIES = {
    'Rhum': ['Rhum blanc', 'Rhum ambre', 'Rhum brun', 'Rhum epice (Spiced rum)',
             'Rhum overproof', 'Rhum blond', 'Rhum noir', 'Malibu (rhum coco)'],
    'Whisky': ['Whiskey bourbon', 'Rye whiskey', 'Scotch whisky', 'Irish whiskey',
               'Canadian whisky', 'Whisky japonais'],
    'Tequila': ['Tequila blanco', 'Tequila reposado', 'Tequila anejo'],
    'Autres spirits': ['Vodka', 'Gin', 'Mezcal', 'Pisco', 'Cachaca', 'Soju',
                       'Sake', 'Baijiu', 'Absinthe', 'Champagne', 'Prosecco'],
    'Liqueurs': ['Aperol', 'Campari', 'Chartreuse verte', 'Chartreuse jaune',
                 'Limoncello', 'Triple sec', 'Cointreau', 'Grand Marnier',
                 'Curacao bleu', 'Kahlua', 'Baileys Irish Cream', 'Amaretto',
                 'Drambuie', 'Sambuca', 'Jagermeister', 'Fernet-Branca',
                 'St-Germain (liqueur de sureau)', 'Benedictine', 'Galliano',
                 'Midori', 'Liqueur de cafe', 'Liqueur de peche',
                 'Liqueur de framboise', 'Creme de menthe verte',
                 'Creme de menthe blanche', 'Creme de cacao blanche',
                 'Creme de cacao', 'Creme de cassis', "Pimm's No. 1", 'Sloe gin',
                 'Amaro Nonino', 'Cherry Heering', 'Maraschino']
}

# Base path pour PyInstaller
if getattr(sys, 'frozen', False):
    BASE_PATH = Path(sys._MEIPASS)
else:
    BASE_PATH = Path(__file__).parent

# Charge recipes.json

def load_recipes(path='recipes.json'):
    file = BASE_PATH / path
    if not file.exists():
        raise FileNotFoundError(f"Le fichier {file} est introuvable.")
    return json.loads(file.read_text(encoding='utf-8'))

try:
    COCKTAILS = load_recipes()
except Exception as e:
    print(f"Erreur de chargement des recettes : {e}")
    COCKTAILS = {}

# Synonymes
SYNONYMS = {
    'Kahlua': 'Liqueur de cafe', 'Liqueur de cafe': 'Liqueur de cafe',
    'Whiskey bourbon': 'Bourbon', 'Bourbon': 'Bourbon',
    'Rye whiskey': 'Rye whiskey'
}

# Recherche des cocktails

def find_cocktails(selected):
    rec_selected = {SYNONYMS.get(s, s) for s in selected}
    expanded = set(rec_selected)
    for items in CATEGORIES.values():
        if any(SYNONYMS.get(it, it) in rec_selected for it in items):
            expanded.update(SYNONYMS.get(it, it) for it in items)
    results = []
    for name, rec in COCKTAILS.items():
        req = set(rec.get('alcohols', {}).keys())
        if req and req.issubset(expanded):
            results.append((name, rec))
    return results

# Tests unitaires
class TestFindCocktails(unittest.TestCase):
    def test_no(self):
        self.assertEqual(find_cocktails(set()), [])

    def test_rhum(self):
        names = [c[0] for c in find_cocktails({'Rhum blanc'})]
        for x in ('Mojito','Pina Colada','Daiquiri'):
            self.assertIn(x, names)

    def test_vodka(self):
        self.assertEqual([c[0] for c in find_cocktails({'Vodka','Triple sec'})], ['Cosmopolitan'])

    def test_liqueur_synonym(self):
        names = [c[0] for c in find_cocktails({'Kahlua'})]
        self.assertIn('Espresso Martini', names)

# Application Qt
class CocktailApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('Proposeur de Cocktails')
        self.resize(800, 600)
        self.selected = set()
        self.init_ui()

    def init_ui(self):
        main_layout = QHBoxLayout(self)

        # Gauche: selection
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        self.search = QLineEdit()
        self.search.setPlaceholderText('Rechercher un alcool...')
        self.search.textChanged.connect(self.filter_checks)
        left_layout.addWidget(self.search)
        self.checks = []
        tabs = QTabWidget()
        for cat, items in CATEGORIES.items():
            tab = QWidget()
            grid = QGridLayout(tab)
            row = col = 0
            for alc in sorted(items):
                cb = QCheckBox(alc)
                self.checks.append(cb)
                grid.addWidget(cb, row, col)
                cb.stateChanged.connect(self.update_selected)
                col += 1
                if col >= 3:
                    col = 0
                    row += 1
            scroll = QScrollArea()
            scroll.setWidgetResizable(True)
            scroll.setWidget(tab)
            tabs.addTab(scroll, cat)
        left_layout.addWidget(tabs)
        btns = QHBoxLayout()
        pb = QPushButton('Proposer'); pb.clicked.connect(self.show_results)
        ql = QPushButton('Quitter'); ql.clicked.connect(self.close)
        btns.addWidget(pb); btns.addWidget(ql)
        left_layout.addLayout(btns)

        # Droite: resultats
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        self.table = QTableWidget(0, 3)
        self.table.setHorizontalHeaderLabels(['Cocktail','Ingredients','A acheter'])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setWordWrap(True)
        self.table.setTextElideMode(Qt.ElideNone)
        right_layout.addWidget(self.table)

        main_layout.addWidget(left_widget)
        main_layout.addWidget(right_widget)

    def filter_checks(self, text):
        for cb in self.checks:
            cb.setVisible(text.lower() in cb.text().lower())

    def update_selected(self):
        self.selected = {cb.text() for cb in self.checks if cb.isChecked()}

    def show_results(self):
        if not self.selected:
            QMessageBox.warning(self, 'Attention', 'Select at least one spirit.')
            return
        lst = find_cocktails(self.selected)
        self.table.setRowCount(len(lst))
        for i, (name, rec) in enumerate(lst):
            ingr = '\n'.join(f"{a}: {q}" for a, q in rec.get('alcohols', {}).items())
            others = '\n'.join(f"{o}: {q}" for o, q in rec.get('others', {}).items()) or 'None'
            self.table.setItem(i, 0, QTableWidgetItem(name))
            self.table.setItem(i, 1, QTableWidgetItem(ingr))
            self.table.setItem(i, 2, QTableWidgetItem(others))
        self.table.resizeRowsToContents()

if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] == 'test':
        unittest.main(argv=[sys.argv[0]])
    else:
        app = QApplication(sys.argv)
        win = CocktailApp()
        win.show()
        sys.exit(app.exec())
