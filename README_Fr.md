# DTLdesktop v1.1-17

Gestionnaire de configurations du bureau Windows.

L'interface console est disponible en français et en anglais. Utilisez
`--lang fr` ou `--lang en` pour forcer une langue ; sinon DTLdesktop suit la
langue du système. En mode interactif, tapez `1` pour changer de langue.

## Quoi ?

DTLdesktop sauvegarde, compare et restaure la position des icônes du bureau, la
configuration détectée des écrans et les fonds propres à chaque écran. Chaque
configuration détectée est conservée séparément :

```text
Desktop\
    DualLandscape\
        icons.json
        monitors.json
        wallpaper.json
```

`wallpaper.json` associe chaque écran à deux fonds :

```json
{
  "configuration": "DualLandscape",
  "monitors": [
    {
      "screen": 2,
      "id": "identifiant fourni par Windows",
      "wallpaper": {
        "landscape": "Piccovaggia.jpg",
        "portrait": "Division2.jpg"
      }
    }
  ]
}
```

Les chemins complets sont enregistrés dans le fichier réel afin que Windows
puisse retrouver les images.

## Pourquoi ?

Windows peut déplacer les icônes lors d'un changement d'écran, d'un branchement
sur un projecteur ou du passage entre le bureau et le télétravail. DTLdesktop
permet de retrouver rapidement une disposition connue.

## Comment ?

Lancez `DTLdesktop.exe`, puis utilisez :

- `S` : mettre à jour directement la configuration sélectionnée au lancement,
  sans demander de nom ;
- `A` : appliquer un profil complet après confirmation ;
- `R` : restaurer uniquement les positions d'icônes ;
- `T` : simuler la restauration sans rien modifier ;
- `D` : diagnostiquer la configuration actuelle ;
- `C` : comparer le bureau avec un profil ;
- `F` : choisir dans l'Explorateur Windows une image pour chaque écran de la
  configuration courante ; aucun chemin ne doit être saisi ;

La ligne de commande accepte aussi :

```powershell
DTLdesktop.exe --save
DTLdesktop.exe --apply DualPortrait
DTLdesktop.exe --test DualLandscape
DTLdesktop.exe --restore DualLandscape
DTLdesktop.exe --diagnose
DTLdesktop.exe --auto
```

Pour une restauration à chaque ouverture de session, placez un raccourci vers
`DTLdesktop.exe --auto` dans le dossier de démarrage Windows.

## Sécurité

Le mode Tester est strictement en lecture seule. Avant une restauration
interactive, DTLdesktop affiche les différences et demande une confirmation.
Les icônes qui n'existent plus sont ignorées et signalées. DTLdesktop ne change
pas la résolution ni la disposition des écrans.

DTLdesktop sélectionne au lancement la configuration correspondant exactement
à la disposition observée, par exemple `DualLandscape` ou `DualPortrait`.
Choisissez les images avec `F`, puis appuyez sur `S` pour mettre à jour cette
configuration. Après rotation d'un écran, l'autre configuration est
sélectionnée automatiquement.

Le sélecteur d'images revient automatiquement dans le dernier dossier utilisé,
y compris après avoir fermé puis relancé DTLdesktop.

Les fonds sont toujours appliqués avec le mode Windows `Remplir`. Aucun autre
mode d'affichage n'est proposé. Après un changement d'orientation, DTLdesktop
réapplique chaque fond, même lorsque le chemin du fichier n'a pas changé, afin
d'empêcher Windows de conserver le bitmap calculé pour l'orientation précédente.

## Application d'un profil

L'action `A` applique un état complet du bureau dans cet ordre :

1. mémorisation temporaire de l'affichage, des fonds et des icônes actuels ;
2. modification groupée de l'orientation, de la résolution et de la disposition
   des écrans ;
3. attente de la stabilisation de Windows ;
4. réapplication de tous les fonds en mode `Remplir` ;
5. restauration des positions d'icônes ;
6. vérification de la configuration obtenue.

Une confirmation est toujours demandée avant le changement. Si Windows refuse
le nouveau mode ou si la vérification échoue, DTLdesktop rétablit
automatiquement l'affichage, les fonds et les icônes précédents.

## Compatibilité

- Windows 10 ou Windows 11 en 64 bits ;
- l'Explorateur Windows doit gérer le bureau ;
- DTLdesktop doit être lancé avec le même niveau de droits que l'Explorateur.

## Construction

```powershell
python -m pip install pyinstaller
pyinstaller --clean DTLdesktop.spec
```

L'exécutable est créé dans `dist\DTLdesktop.exe`.
