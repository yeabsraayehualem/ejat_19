clear
docker compose down && docker compose up -d --build

sleep 2

docker exec -it ejat_19 tail -f /etc/odoo/server.log