#!/bin/sh
set -e

# Restore your School Results database from Backblaze if the server wiped it
litestream restore -if-db-not-exists -if-replica-exists /app/School_Results_Database.db

# Restore your second database file
litestream restore -if-db-not-exists -if-replica-exists /app/passkey.db

# Run Litestream replication and start your Python app
exec litestream replicate -exec "python loginPage.py"
