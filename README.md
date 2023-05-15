# Cookie clicker bot

Bot to play [the cookie clicker game](https://orteil.dashnet.org/cookieclicker/).

### You can endlessly look at flowing water, burning fire and... cookie clicker bot workflow😂

## Stack: Python, Selenium, Docker.

## Build:

- Create dir logs with permissions and build docker-compose:
```bash
mkdir -m 777 -p logs && docker compose build
```

## Launch methods:
- Primitive way (bot will be working for 10 minutes, by default):
```bash
docker-compose up
```

- With setting the game time in minutes (e.g. 2 minutes):
```bash
docker compose run --rm --env GAME_TIME=2 bot
```
