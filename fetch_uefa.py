#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Récupère sur UEFA.com les matchs et les classements des trois coupes d'Europe,
puis écrit un fichier JSON compact par compétition dans data/.

    python3 fetch_uefa.py

L'API d'UEFA.com n'autorise que son propre site à l'appeler depuis un
navigateur. Ce script tourne donc côté serveur, dans GitHub Actions, et
l'application ne lit que les fichiers de data/, servis par sa propre origine.
"""
import io
import json
import os
import sys
import urllib.error
import urllib.request
from datetime import datetime, timezone

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, 'data')
# Saison ciblée. UEFA nomme une saison par son année de finale : 2027 pour
# 2026/27. Surchargeable pour rejouer une saison passée : UEFA_SEASON=2026.
SEASON = os.environ.get('UEFA_SEASON', '2027')

COMPETITIONS = [
    ('UCL', '1'),
    ('UEL', '14'),
    ('UECL', '2019'),
]

# La Supercoupe d'Europe ouvre la saison 2026/27 mais UEFA.com la rattache à la
# saison précédente, celle des deux vainqueurs qui s'y affrontent.
SUPERCOUPE_ID = '9'
SUPERCOUPE_SEASON = str(int(SEASON) - 1)

# Tours de la phase à élimination directe, dans l'ordre, avec la clé de barème
# utilisée par le calculateur.
KO_ROUNDS = [
    ('FINAL_TOURNAMENT_PLAY_OFF', 'barrages'),
    ('ROUND_OF_16', 'r16'),
    ('QUARTER_FINALS', 'qf'),
    ('SEMIFINAL', 'sf'),
    ('FINAL', 'final'),
]
KO_BY_TYPE = dict(KO_ROUNDS)
KO_ORDER = [k for _, k in KO_ROUNDS]

# Tours de qualification, pour information.
QUALIF_BY_TYPE = {
    'FIRST_QUALIFYING': 'Q1',
    'SECOND_QUALIFYING': 'Q2',
    'THIRD_QUALIFYING': 'Q3',
    'PLAY_OFF': 'PO',
}

HEADERS = {
    'Accept': 'application/json',
    'User-Agent': 'prize-money-2627/1.0 (+https://github.com/FrancoisManardo/prize-money-2627)',
}


def get(url):
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=45) as r:
        return json.loads(r.read().decode('utf-8'))


def fr(node, field, fallback=''):
    """Nom français d'un objet UEFA, avec repli sur l'anglais."""
    tr = (node or {}).get('translations', {}).get(field, {})
    return tr.get('FR') or tr.get('EN') or fallback


def team_of(node):
    if not node:
        return None
    return {
        'id': node.get('id'),
        'n': fr(node, 'displayName', node.get('internationalName', '')),
        'full': fr(node, 'displayOfficialName', fr(node, 'displayName', node.get('internationalName', ''))),
        'code': node.get('teamCode'),
        'pays': node.get('countryCode'),
    }


def fetch_matches(competition_id):
    out, offset = [], 0
    while True:
        url = ('https://match.uefa.com/v5/matches?competitionId=%s&seasonYear=%s&offset=%d&limit=100'
               % (competition_id, SEASON, offset))
        page = get(url)
        if not page:
            break
        out.extend(page)
        if len(page) < 100:
            break
        offset += 100
        if offset > 1000:
            break
    return out


def fetch_standings(competition_id):
    url = ('https://standings.uefa.com/v1/standings?competitionId=%s&seasonYear=%s&phase=TOURNAMENT'
           % (competition_id, SEASON))
    try:
        return get(url)
    except urllib.error.HTTPError:
        return []


def simple_match(m):
    score = m.get('score') or {}
    total = score.get('total') or {}
    regular = score.get('regular') or {}
    penalties = score.get('penalty') or {}
    ko = m.get('kickOffTime') or {}
    row = {
        'id': m.get('id'),
        'h': team_of(m.get('homeTeam')),
        'a': team_of(m.get('awayTeam')),
        'date': ko.get('date'),
        'heure': (ko.get('dateTime') or '')[11:16],
        'statut': m.get('status'),
    }
    if total.get('home') is not None:
        row['hg'] = total.get('home')
        row['ag'] = total.get('away')
    if regular.get('home') is not None and regular != total:
        row['reg'] = [regular.get('home'), regular.get('away')]
    if penalties.get('home') is not None:
        row['tab'] = [penalties.get('home'), penalties.get('away')]
    winner = ((m.get('winner') or {}).get('match') or {}).get('team') or {}
    if winner.get('id'):
        row['vainqueur'] = winner.get('id')
    return row


def build(comp, competition_id):
    matches = fetch_matches(competition_id)
    standings = fetch_standings(competition_id)

    league = {}
    knockout = {}
    qualif = {}

    for m in matches:
        rnd = m.get('round') or {}
        meta = rnd.get('metaData') or {}
        rtype = meta.get('type')
        phase = m.get('competitionPhase')
        row = simple_match(m)

        if phase == 'QUALIFYING':
            key = QUALIF_BY_TYPE.get(rtype, rtype)
            qualif.setdefault(key, []).append(row)
        elif rtype == 'GROUP_STANDINGS':
            md = (m.get('matchday') or {}).get('sequenceNumber')
            if md:
                league.setdefault(str(md), []).append(row)
        elif rtype in KO_BY_TYPE:
            key = KO_BY_TYPE[rtype]
            bucket = knockout.setdefault(key, {'cle': key, 'nom': fr(rnd, 'name', meta.get('name', key)), 'matchs': []})
            bucket['matchs'].append(row)

    for md in league:
        league[md].sort(key=lambda r: (r.get('date') or '', r.get('heure') or ''))
    for key in knockout:
        knockout[key]['matchs'].sort(key=lambda r: (r.get('date') or '', r.get('heure') or ''))

    table = []
    if standings:
        for item in (standings[0].get('items') or []):
            t = team_of(item.get('team'))
            table.append({
                'rang': item.get('rank'),
                'equipe': t,
                'j': item.get('played'),
                'g': item.get('won'),
                'n': item.get('drawn'),
                'p': item.get('lost'),
                'bp': item.get('goalsFor'),
                'bc': item.get('goalsAgainst'),
                'diff': item.get('goalDifference'),
                'pts': item.get('points'),
            })
        table.sort(key=lambda r: (r['rang'] is None, r['rang']))

    joues = sum(1 for md in league.values() for r in md if r.get('statut') == 'FINISHED')
    return {
        'comp': comp,
        'competitionId': competition_id,
        'saison': SEASON,
        'maj': datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ'),
        'phaseDeLigue': league,
        'phaseFinale': [knockout[k] for k in KO_ORDER if k in knockout],
        'qualifications': qualif,
        'classement': table,
        'matchsJoues': joues,
    }


def build_supercoupe():
    url = ('https://match.uefa.com/v5/matches?competitionId=%s&seasonYear=%s&offset=0&limit=10'
           % (SUPERCOUPE_ID, SUPERCOUPE_SEASON))
    matches = get(url)
    if not matches:
        return None
    m = matches[0]
    row = simple_match(m)
    row['saisonUefa'] = SUPERCOUPE_SEASON
    row['stade'] = ((m.get('stadium') or {}).get('translations', {}).get('officialName', {}) or {}).get('FR')
    return row


def main():
    os.makedirs(DATA, exist_ok=True)
    resume = []

    try:
        sc = build_supercoupe()
    except Exception as exc:
        sc = None
        print('Supercoupe : echec (%s)' % exc, file=sys.stderr)
    if sc:
        io.open(os.path.join(DATA, 'supercoupe.json'), 'w', encoding='utf-8').write(
            json.dumps(sc, ensure_ascii=False, separators=(',', ':'), sort_keys=True))
        print('SCUP  %s %s-%s %s (%s)' % (sc['h']['n'], sc.get('hg'), sc.get('ag'), sc['a']['n'], sc.get('statut')))
    for comp, cid in COMPETITIONS:
        try:
            payload = build(comp, cid)
        except Exception as exc:  # une compétition en échec ne doit pas bloquer les autres
            print('%s : echec (%s)' % (comp, exc), file=sys.stderr)
            continue
        path = os.path.join(DATA, comp.lower() + '.json')
        text = json.dumps(payload, ensure_ascii=False, separators=(',', ':'), sort_keys=True)
        io.open(path, 'w', encoding='utf-8').write(text)
        resume.append({
            'comp': comp,
            'journees': len(payload['phaseDeLigue']),
            'matchsJoues': payload['matchsJoues'],
            'toursFinale': len(payload['phaseFinale']),
            'classement': len(payload['classement']),
            'octets': len(text.encode('utf-8')),
        })
        print('%-5s %2d journees, %3d matchs joues, %d tour(s) de phase finale, %2d lignes de classement, %d Ko'
              % (comp, len(payload['phaseDeLigue']), payload['matchsJoues'],
                 len(payload['phaseFinale']), len(payload['classement']),
                 round(len(text.encode('utf-8')) / 1024)))

    if not resume:
        sys.exit('Aucune competition recuperee.')

    index = {
        'maj': datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ'),
        'competitions': resume,
    }
    io.open(os.path.join(DATA, 'index.json'), 'w', encoding='utf-8').write(
        json.dumps(index, ensure_ascii=False, indent=1))


if __name__ == '__main__':
    main()
