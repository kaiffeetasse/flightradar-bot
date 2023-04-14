#git stash
git pull
docker build --tag flightradar-bot:latest .
chmod +x update.sh
docker compose down
docker compose up -d
