# Prize Money 26/27 — application iPhone

Application web installable sur l'écran d'accueil de l'iPhone. Elle contient le
calculateur de prize money UEFA 2026/27 et le suivi de l'évolution des gains
par club, journée après journée.

## Installer sur l'iPhone

1. Ouvrir l'adresse de l'application dans **Safari** (pas Chrome : seul Safari
   sait installer sur l'écran d'accueil).
2. Bouton **Partager**, puis **Sur l'écran d'accueil**.
3. Laisser le nom « Prize Money », puis **Ajouter**.

L'application s'ouvre alors en plein écran, sans barre d'adresse, et fonctionne
sans connexion une fois chargée la première fois.

## Mettre à jour après une nouvelle journée

Deux façons de faire, au choix.

**Depuis l'iPhone, sans rien réinstaller.** Onglet « Saison & évolution »,
dernier panneau, coller les scores puis « Enregistrer la journée » :

    UCL MD2
    Arsenal 2-1 Real Madrid
    Bayern Munich 0-0 Liverpool

Les résultats saisis restent dans l'application, sur l'appareil.

**Depuis le Mac, pour que la journée soit livrée avec l'application.** Modifier
le calculateur `../uefa-prize-money-2026-27.html`, puis :

    cd ~/Desktop/uefa-prize-money-app
    python3 build.py
    git add -A && git commit -m "Journée N" && git push

La mise en ligne prend une minute environ. Sur l'iPhone, fermer puis rouvrir
l'application suffit à récupérer la nouvelle version.

## Contenu du dossier

| Fichier | Rôle |
|---|---|
| `build.py` | Régénère `index.html` depuis le calculateur du Bureau |
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
