#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Régénère l'application installable à partir du calculateur du Bureau.

    python3 build.py

Le calculateur reste la source unique : ce script en fait une copie et y ajoute
seulement ce qu'exige une application installée (manifeste, icônes, mode hors
ligne, marges de la barre d'état). Relancez-le après chaque modification du
calculateur, puis remettez le dossier en ligne.
"""
import hashlib
import io
import re
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
SOURCE = os.path.join(os.path.dirname(HERE), 'uefa-prize-money-2026-27.html')
TARGET = os.path.join(HERE, 'index.html')

HEAD = """<link rel="manifest" href="manifest.webmanifest" />
<meta name="apple-mobile-web-app-capable" content="yes" />
<meta name="mobile-web-app-capable" content="yes" />
<meta name="apple-mobile-web-app-status-bar-style" content="default" />
<meta name="apple-mobile-web-app-title" content="Prize Money" />
<meta name="theme-color" content="#0B1C3D" />
<link rel="apple-touch-icon" href="icons/icon-uefa-180.png" />
<link rel="icon" type="image/png" href="icons/icon-uefa-192.png" />
<style>
  /* Application installée : laisser passer la barre d'état et la barre d'accueil. */
  @media (display-mode: standalone){
    .letterhead{ padding-top: calc(16px + env(safe-area-inset-top)); }
    body{ overscroll-behavior-y: none; }
  }
</style>"""

FOOT = """<script>
if('serviceWorker' in navigator){
  window.addEventListener('load', function(){
    navigator.serviceWorker.register('sw.js').catch(function(){ /* hors ligne simplement indisponible */ });
  });
}
</script>"""

ANCHOR = '<meta name="viewport" content="width=device-width, initial-scale=1.0, viewport-fit=cover" />'


def main():
    if not os.path.exists(SOURCE):
        sys.exit('Calculateur introuvable : ' + SOURCE)
    html = io.open(SOURCE, encoding='utf-8').read()

    if html.count(ANCHOR) != 1:
        sys.exit('Balise viewport introuvable dans le calculateur : structure inattendue.')
    if html.count('</body>') != 1:
        sys.exit('Balise </body> introuvable dans le calculateur : structure inattendue.')

    html = html.replace(ANCHOR, ANCHOR + '\n' + HEAD)
    html = html.replace('</body>', FOOT + '\n</body>')
    io.open(TARGET, 'w', encoding='utf-8').write(html)

    sw_path = os.path.join(HERE, 'sw.js')
    sw = io.open(sw_path, encoding='utf-8').read()
    # La version du cache dépend de la page et du service worker lui-même, sa
    # propre ligne de version exclue pour ne pas boucler.
    empreinte = html + re.sub(r"const VERSION = '[^']*'", '', sw)
    build = hashlib.sha1(empreinte.encode('utf-8')).hexdigest()[:10]
    start = sw.index("const VERSION = '") + len("const VERSION = '")
    end = sw.index("'", start)
    sw = sw[:start] + build + sw[end:]
    io.open(sw_path, 'w', encoding='utf-8').write(sw)

    print('index.html régénéré depuis ' + os.path.basename(SOURCE))
    print('version du cache hors ligne : ' + build)
    print('taille : ' + str(round(len(html.encode('utf-8')) / 1024)) + ' Ko')


if __name__ == '__main__':
    main()
