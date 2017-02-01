# Information taken from https://docs.docker.com/registry/deploying/


# Name of the registry
export REGISTRY_NAME=private

# Directory where htpasswd file will be put as well as all Docker images data
export REGISTRY_DATA="$HOME/docker/registry/$REGISTRY_NAME/data"

# Localhost port that will be used for registry
export REGISTRY_PORT=2016

# DOMAIN is necessary to retreive SSL certification
# files installed by Let's Encrypt
export DOMAIN=sandbox.brainvisa.info


if [ ! -d "$REGISTRY_DATA" ]; then
    mkdir --parents $REGISTRY_DATA
fi
cd "$REGISTRY_DATA"
cd ..
envsubst < config-template.yaml > "$REGISTRY_DATA/config.yaml"
envsubst < docker-compose-template.yaml > "$REGISTRY_DATA/docker-compose.yaml"
# Interactively set a password for "brainvisa" user in 
htpasswd -cB "$REGISTRY_DATA/htpasswd" "brainvisa"
# Start the registry server
cd "$REGISTRY_DATA"
docker-compose up -d

