# Prize Money 26/27 — application iPhone

Application web installable sur l'écran d'accueil de l'iPhone. Elle suit la
saison 2026/27 des trois coupes d'Europe et calcule le prize money de chaque
club au fil des matchs.

Quatre onglets : la fiche d'un club suivi, les matchs journée par journée puis
tour par tour, le classement, et les gains avec leur évolution.

## Installer sur l'iPhone

1. Ouvrir l'adresse de l'application dans **Safari** (pas Chrome : seul Safari
   sait installer sur l'écran d'accueil).
2. Bouton **Partager**, puis **Sur l'écran d'accueil**.
3. Laisser le nom « Prize Money », puis **Ajouter**.

L'application s'ouvre alors en plein écran, sans barre d'adresse, et fonctionne
sans connexion une fois chargée la première fois.

## Les résultats se mettent à jour tout seuls

`fetch_uefa.py` relève sur UEFA.com les matchs, les classements et les
calendriers des trois compétitions, saison 2026/27 : tours de qualification,
Supercoupe d'Europe, phase de ligue puis phase à élimination directe. Il écrit
un fichier par compétition dans `data/`.

GitHub Actions le relance toutes les deux heures, et toutes les vingt minutes
du mardi au jeudi soir pendant les matchs. Quand un score change, le workflow
publie les nouveaux fichiers et l'application les reprend à sa prochaine
ouverture. Rien à faire à la main.

L'API d'UEFA.com n'autorise que son propre site à l'appeler depuis un
navigateur, d'où ce détour par un relevé côté serveur.

Pour forcer un relevé immédiat :

    cd ~/Desktop/uefa-prize-money-app
    python3 fetch_uefa.py
    git add data && git commit -m "Relevé manuel" && git push

Ou, sur GitHub, onglet Actions, workflow « Mise à jour des données UEFA »,
bouton « Run workflow ».

## Saisir un résultat à la main

Utile hors ligne, ou avant le relevé suivant. Onglet « Gains », dernier
panneau, coller les scores puis « Enregistrer la journée » :

    UCL MD2
    Arsenal 2-1 Real Madrid
    Bayern Munich 0-0 Liverpool

Les résultats officiels reprennent la main dès qu'ils arrivent.

## Modifier le calculateur lui-même

    cd ~/Desktop/uefa-prize-money-app
    python3 build.py
    git add -A && git commit -m "..." && git push

La mise en ligne prend une minute environ. Sur l'iPhone, fermer puis rouvrir
l'application suffit à récupérer la nouvelle version.

## Contenu du dossier

| Fichier | Rôle |
|---|---|
| `build.py` | Régénère `index.html` depuis le calculateur du Bureau |
| `fetch_uefa.py` | Relève matchs et classements sur UEFA.com |
| `data/` | Résultats relevés, un fichier par compétition |
| `.github/workflows/` | Relevé automatique plusieurs fois par jour |
| `index.html` | Fichier généré, ne pas modifier à la main |
| `manifest.webmanifest` | Nom, icône et mode plein écran de l'application |
| `sw.js` | Cache hors ligne, sa version change à chaque build |
| `icons/` | Icônes de l'écran d'accueil et leur source `icon.html` |

Le calculateur `~/Desktop/uefa-prize-money-2026-27.html` reste la source unique.
Toute modification se fait là-bas, puis `python3 build.py` la reporte ici.

## Données

Les clubs suivis et les journées saisies sont enregistrés dans le navigateur de
l'appareil. Ils ne quittent jamais le téléphone et ne sont pas synchronisés
entre l'iPhone et le Mac. Chaque appareil garde donc sa propre saisie.
