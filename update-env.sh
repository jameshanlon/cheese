#!/bin/bash
source CONFIG
rm -rf docker-compose.yml
envsubst < docker-compose.yml.in > docker-compose.yml
