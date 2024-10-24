# Basic Docker commands
build_image:
	docker build -t memento-vault .

run_container:
	docker run -d --name memento-vault-container -v .:/app -p 9001:9000 memento-vault

# Add helpful commands for Docker management
stop_container:
	docker stop memento-vault-container

remove_container:
	docker rm memento-vault-container

# Clean up command
clean: stop_container remove_container
	docker rmi memento-vault

# Development commands
dev: build_image run_container

# Restart command
restart: stop_container remove_container run_container

# Show container logs
logs:
	docker logs -f memento-vault-container

# Show container status
status:
	docker ps -a | grep memento-vault

.PHONY: build_image run_container stop_container remove_container clean dev restart logs status