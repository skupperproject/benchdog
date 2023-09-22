#!/bin/bash

PGPASSWORD="$POSTGRES_PASSWORD"

exec pgbench --username "$POSTGRES_USER" --initialize
