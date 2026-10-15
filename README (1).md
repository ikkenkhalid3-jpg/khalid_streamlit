# Tableau de bord Santé — Rendez-vous

Cette application **Streamlit** analyse les rendez-vous de santé enregistrés de janvier à août 2026. Elle utilise **pandas** pour préparer et analyser les données et **matplotlib** pour créer les graphiques. Le classeur fourni indique que les données sont fictives.

## Fichiers nécessaires

Placez ces fichiers dans un même dossier :

- `output.py` : code de l'application Streamlit ;
- `requirements.txt` : liste des bibliothèques Python nécessaires ;
- `06_Sante.xlsm` : classeur Excel contenant les données.

Le classeur Excel peut aussi être importé directement dans l'application. Il n'est pas nécessaire de le placer dans le même dossier si vous utilisez le bouton d'importation.

## Questions traitées

Le tableau de bord répond aux six questions suivantes :

1. Quel service reçoit le plus de rendez-vous ?
2. Quels sont les taux de rendez-vous honorés, d'absences et d'annulations par service ?
3. Quels services présentent les délais de rendez-vous les plus longs ?
4. Comment le temps d'attente moyen varie-t-il selon la ville pour les rendez-vous honorés ?
5. Comment le volume des rendez-vous et le nombre d'absences évoluent-ils chaque mois ?
6. Quelles améliorations organisationnelles peut-on proposer à partir des résultats ?

## Installation sous Windows

1. Installez **Python 3.10 ou une version plus récente**. Pendant l'installation, cochez l'option permettant d'ajouter Python au `PATH` si elle est proposée.
2. Ouvrez le dossier contenant `output.py` et `requirements.txt`.
3. Dans ce dossier, ouvrez un terminal ou PowerShell.
4. Créez un environnement virtuel :

```powershell
python -m venv .venv
```

5.Activez l'environnement virtuel :

```powershell
.venv\Scripts\Activate.ps1
```

Si PowerShell bloque l'activation, vous pouvez ouvrir l'invite de commandes (`cmd`) et exécuter :

```bat
.venv\Scripts\activate.bat
```

6.Installez les dépendances :

```powershell
python -m pip install -r requirements.txt
```

7.Lancez l'application :

```powershell
python -m streamlit run output.py
```

Streamlit affichera une adresse locale, généralement `http://localhost:8501`. Ouvrez cette adresse dans votre navigateur.

## Chargement du classeur Excel

L'application cherche automatiquement un fichier nommé `06_Sante.xlsm` dans le même dossier que `output.py`. Si le fichier n'est pas trouvé, importez-le à l'aide du champ prévu dans la barre latérale.

Le code lit la feuille Excel nommée `Données` et utilise la troisième ligne comme ligne d'en-tête (`header=2`). Si le nom de la feuille ou la ligne des en-têtes change, il faudra adapter les paramètres dans `output.py`.

## Utilisation

- Utilisez les filtres de la barre latérale pour sélectionner les services, les villes, les statuts, les canaux de réservation et la période.
- Les indicateurs, tableaux et graphiques se mettent à jour selon les filtres sélectionnés.
- Ouvrez la section **Voir les données filtrées** pour consulter les lignes retenues ou les télécharger au format CSV.
- Si aucun rendez-vous ne correspond aux filtres, élargissez la sélection.

## Méthodologie et limites

- Les taux de rendez-vous honorés, d'absences et d'annulations sont calculés sur l'ensemble des rendez-vous correspondant aux filtres.
- Le délai moyen est calculé sur les valeurs renseignées. L'attente, la durée de consultation et la satisfaction sont calculées uniquement pour les rendez-vous dont le statut est `Honoré`, et seulement lorsque les valeurs correspondantes sont disponibles.
- Les valeurs manquantes ne sont pas remplacées par zéro.
- Les résultats sont descriptifs : une différence entre services ou entre villes ne suffit pas à établir une relation de cause à effet.
- Les résultats peuvent changer lorsque les filtres sont modifiés.

## Déploiement en ligne avec Streamlit Community Cloud

1. Créez un dépôt GitHub contenant `output.py`, `requirements.txt` et ce fichier `README.md`.
2. Ne publiez le classeur `06_Sante.xlsm` que si vous êtes autorisé à le partager. Pour ce projet, vous pouvez aussi laisser les utilisateurs importer le classeur dans l'application plutôt que de le déposer sur GitHub.
3. Dans Streamlit Community Cloud, créez une application et sélectionnez le dépôt GitHub, la branche et `output.py` comme fichier principal.
4. Lancez le déploiement.

**Confidentialité :** ne publiez jamais de données de santé réelles ou permettant d'identifier des personnes dans un dépôt public. Vérifiez également les règles de confidentialité de votre organisation avant tout déploiement.
