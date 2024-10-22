#! /bin/bash
docker exec -it mongo bash
mongo --eval "db.getSiblingDB('test_db').test_collection.insert({ name: 'test' })"
mongo --eval "db.getSiblingDB('test_db').test_collection.find().pretty()"

