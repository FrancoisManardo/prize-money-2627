#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Rapproche les logos de clubs du dossier source des équipes relevées sur
UEFA.com, puis écrit dans assets/logos/ un PNG par identifiant d'équipe.

    python3 match_logos.py [--dry]

Les fichiers sont nommés par l'identifiant UEFA, ce qui évite toute table de
correspondance à l'exécution : l'application demande assets/logos/<id>.png.
"""
import io
import json
import os
import re
import shutil
import subprocess
import sys
import unicodedata

HERE = os.path.dirname(os.path.abspath(__file__))
SOURCE = '/Users/francoismanardo/Documents/Dev. app. Frais C. Code/deploy/assets/logos'
DEST = os.path.join(HERE, 'assets', 'logos')
DATA = os.path.join(HERE, 'data')
TAILLE = 96

# Rapprochements que la comparaison de chaînes ne trouve pas seule.
MANUEL = {
    'atletico-madrid-atleti': ['atletico de madrid', 'atleti'],
    'fc-internazionale-milano': ['inter'],
    'gnk-dinamo': ['gnk dinamo', 'dinamo zagreb'],
    'fk-bod-glimt': ['bodo/glimt', 'bodø/glimt'],
    'r-union-saint-gilloise': ['union sg', 'royale union saint-gilloise'],
    'lillestr-m-sk': ['lillestrom', 'lillestrøm'],
    'brei-ablik': ['breidablik'],
    'jagiellonia-bia-ystok': ['jagiellonia bialystok', 'jagiellonia białystok'],
    'fc-dynamo-kiev': ['dynamo kyiv', 'dinamo kiev'],
    'losc-lille': ['lille'],
    'rc-lens': ['lens'],
    'paris-saint-germain': ['paris', 'psg'],
    'fotbal-club-fcsb': ['fcsb'],
    'u-craiova-1948': ['u. craiova', 'universitatea craiova'],
    'sk-slovan-bratislava': ['s. bratislava', 'slovan bratislava'],
    'hapoel-beer-sheva-fc': ['h. beer-sheva', 'hapoel beer sheva'],
    'manchester-united': ['man utd', 'manchester united'],
    'manchester-city-fc': ['man city', 'manchester city'],
    'n-e-c-nijmegen': ['n.e.c.', 'nec nijmegen'],
    'kups-kuopio': ['kups kuopio', 'kups'],
    'fc-kairat-almaty': ['kairat almaty', 'kairat'],
    'lincoln-red-imps-fc': ['l. red imps', 'lincoln red imps'],
    'fk-kauno-zalgiris': ['kauno zalgiris', 'kauno žalgiris'],
    'kks-lech-poznan': ['lech poznan', 'lech poznań'],
    'agf-aarhus': ['aarhus', 'agf'],
    'fc-iberia-1999-tbilisi': ['iberia tbilisi', 'iberia 1999'],
    'k-sint-truidense-vv': ['sint-truidense', 'stvv'],
    'sk-slavia-praha': ['slavia praha', 'slavia prague'],
    'ac-sparta-praha': ['sparta praha', 'sparta prague'],
    'fc-bayern-munchen': ['bayern munchen', 'bayern münchen', 'bayern munich'],
    'borussia-dortmund': ['b. dortmund', 'borussia dortmund'],
    'fc-barcelona': ['barcelona', 'fc barcelone', 'barcelone'],
    'inter-club-escaldes': ['inter escaldes'],
    'pfc-cska-sofia': ['cska sofia'],
    'pfc-levski-sofia': ['levski sofia'],
    'olympique-lyonnais': ['lyon'],
    'celtic-fc': ['celtic'],
    'heart-of-midlothian-fc': ['hearts'],
    'nk-celje': ['celje'],
    'fc-ararat-armenia': ['ararat-armenia'],
    'riga-fc': ['riga'],
    'fk-borac': ['borac'],
    'kf-egnatia': ['egnatia'],
    'hnk-hajduk-split': ['hajduk split'],
    'fc-midtjylland': ['midtjylland'],
    'mjallby-aif': ['mjallby', 'mjällby'],
    'pafos-fc': ['pafos'],
    'sabah-fc': ['sabah'],
    'fc-thun': ['thun'],
    'trabzonspor-as': ['trabzonspor'],
    'fc-twente': ['twente'],
    'viking': ['viking'],
    'villarreal-cf': ['villarreal'],
    'fc-shakhtar-donetsk': ['shakhtar', 'shakhtar donetsk'],
    'psv-eindhoven': ['psv', 'psv eindhoven'],
    'real-betis-balompie': ['real betis', 'betis'],
    'sporting-clube-de-portugal': ['sporting cp'],
    'ssc-napoli': ['napoli'],
    'as-roma': ['roma'],
    'fenerbahce-a-s': ['fenerbahce', 'fenerbahçe'],
    'galatasaray-a-s': ['galatasaray'],
    'club-brugge': ['club brugge', 'club bruges'],
    'aston-villa-fc': ['aston villa'],
    'arsenal-fc': ['arsenal'],
    'liverpool-fc': ['liverpool'],
    'como-1907': ['como'],
    'rb-leipzig': ['leipzig'],
    'vfb-stuttgart': ['stuttgart'],
    'fc-porto': ['porto'],
    'real-madrid-cf': ['real madrid'],
    'aek-athens': ['aek athens', 'aek athènes'],
    'lask': ['lask'],
    'feyenoord': ['feyenoord'],
    'omonoia-fc': ['omonia', 'omonoia'],
    'olympiacos-fc': ['olympiacos'],
    'sk-sturm-graz': ['sturm graz'],
    'qarabag-fk': ['qarabag', 'qarabağ'],
    'fk-crvena-zvezda': ['crvena zvezda'],
    'rsc-anderlecht': ['anderlecht'],
    'az-alkmaar': ['az alkmaar', 'az'],
}


def slugify(s):
    s = unicodedata.normalize('NFD', s or '')
    s = ''.join(c for c in s if unicodedata.category(c) != 'Mn')
    s = s.lower().replace('ø', 'o').replace('ł', 'l').replace('æ', 'ae')
    s = re.sub(r'[^a-z0-9]+', '-', s).strip('-')
    return s


def tokens(s):
    bruit = {'fc', 'cf', 'sk', 'ac', 'as', 'sc', 'afc', 'club', 'de', 'du', 'the',
             'gmbh', 'a', 's', 'vv', 'k', 'kf', 'fk', 'nk', 'hnk', 'pfc', 'kks', 'rc', 'rsc'}
    return {t for t in slugify(s).split('-') if t and t not in bruit and len(t) > 2}


def charger_equipes():
    equipes = {}
    for nom in ['ucl', 'uel', 'uecl']:
        chemin = os.path.join(DATA, nom + '.json')
        if not os.path.exists(chemin):
            continue
        d = json.load(io.open(chemin, encoding='utf-8'))
        comp = d['comp']
        for r in d.get('classement', []):
            e = r.get('equipe')
            if e and e.get('id'):
                equipes[e['id']] = dict(e, comp=comp)
        for md in d.get('phaseDeLigue', {}).values():
            for m in md:
                for cle in ('h', 'a'):
                    e = m.get(cle)
                    if e and e.get('id'):
                        equipes.setdefault(e['id'], dict(e, comp=comp))
    chemin = os.path.join(DATA, 'supercoupe.json')
    if os.path.exists(chemin):
        m = json.load(io.open(chemin, encoding='utf-8'))
        for cle in ('h', 'a'):
            e = m.get(cle)
            if e and e.get('id'):
                equipes.setdefault(e['id'], dict(e, comp='SCUP'))
    return equipes


def index_source():
    index = {}
    for slug in os.listdir(SOURCE):
        chemin = os.path.join(SOURCE, slug, 'light.png')
        if os.path.isfile(chemin):
            index[slug] = chemin
    return index


def apparier(equipe, index):
    candidats = [equipe.get('full', ''), equipe.get('n', '')]
    for c in candidats:
        s = slugify(c)
        if s in index:
            return s, 'exact'
    # Rapprochements déclarés à la main.
    noms = {slugify(c) for c in candidats}
    for slug, alias in MANUEL.items():
        if slug in index and noms & {slugify(a) for a in alias}:
            return slug, 'manuel'
    # Meilleur recouvrement de mots significatifs.
    mots = tokens(equipe.get('full', '')) | tokens(equipe.get('n', ''))
    meilleur, score = None, 0
    for slug in index:
        commun = len(mots & tokens(slug))
        if commun > score:
            meilleur, score = slug, commun
    if meilleur and score >= 1:
        return meilleur, 'mots'
    return None, None


def main():
    dry = '--dry' in sys.argv
    equipes = charger_equipes()
    index = index_source()
    print('%d équipes relevées, %d logos disponibles' % (len(equipes), len(index)))

    if not dry:
        os.makedirs(DEST, exist_ok=True)

    trouves, manquants, par_methode = {}, [], {}
    for eid, e in sorted(equipes.items(), key=lambda kv: kv[1]['n']):
        slug, methode = apparier(e, index)
        if not slug:
            manquants.append(e)
            continue
        trouves[eid] = slug
        par_methode[methode] = par_methode.get(methode, 0) + 1
        if dry:
            continue
        cible = os.path.join(DEST, eid + '.png')
        shutil.copyfile(index[slug], cible)
        subprocess.run(['sips', '-s', 'format', 'png', '-Z', str(TAILLE), cible, '--out', cible],
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False)

    print('appariés : %d (%s)' % (len(trouves), ', '.join('%s %d' % kv for kv in sorted(par_methode.items()))))
    if manquants:
        print('sans logo : %d' % len(manquants))
        for e in manquants:
            print('   %-24s %-32s %s' % (e['n'], e.get('full', ''), e['comp']))

    if not dry:
        io.open(os.path.join(DEST, 'index.json'), 'w', encoding='utf-8').write(
            json.dumps({'logos': trouves}, ensure_ascii=False, indent=1, sort_keys=True))
        total = sum(os.path.getsize(os.path.join(DEST, f)) for f in os.listdir(DEST) if f.endswith('.png'))
        print('assets/logos : %d fichiers, %d Ko' % (len(trouves), round(total / 1024)))


if __name__ == '__main__':
    main()
