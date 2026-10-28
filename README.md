# supervision-reseau

Application web de supervision réseau : elle vérifie en continu des serveurs, postes et imprimantes, et affiche leur état en temps réel sur un tableau de bord.

Projet Python réalisé à Télécom SudParis par Alban ROBERT et Zakari HADJERES.

## Lancer le projet

Prérequis : Docker (Linux ou macOS).

```bash
git clone https://github.com/Alban091/supervision-reseau.git
cd supervision-reseau
docker compose up -d
```

L'application est ensuite disponible sur http://localhost:8080.

Pour tout arrêter : `docker compose down`.

## Compte par défaut

`admin` / `projetinfo1A`, créé automatiquement au premier lancement.

## Architecture

- `db` : base PostgreSQL 16
- `web` : application Django servie par Gunicorn
- `nginx` : reverse proxy sur le port 8080, qui sert aussi les fichiers statiques et les médias

Au démarrage, le conteneur `web` applique les migrations, copie les fichiers statiques et crée le compte admin s'il n'existe pas.

## Tests

```bash
docker compose exec web python manage.py test
```

## Roadmap

- [x] Projet Django et Docker (PostgreSQL, Gunicorn, Nginx)
- [ ] Parc de test Docker
- [ ] Modèles et administration
- [ ] Supervision ping et TCP
- [ ] Tableau de bord en temps réel
- [ ] Équipements qui parlent (lot 1)

## Modèle de données

À venir.
