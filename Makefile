.PHONY: install bootstrap validate homelab-up homelab-down homelab-logs

install:
	./scripts/install.sh

bootstrap:
	./scripts/bootstrap.sh

validate:
	./scripts/validate-repo.sh

homelab-up:
	cd homelab && docker compose up -d

homelab-down:
	cd homelab && docker compose down

homelab-logs:
	cd homelab && docker compose logs -f
