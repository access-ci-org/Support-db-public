#!/usr/bin/env bash

## ASSUMING CONDA IS INSTALLED

ENV_NAME=DB_ENV

# create the environment
echo "Creating the environment"
conda create -p ./env/$ENV_NAME -y

# remove env prefix from shell prompts
echo "Removing prefix from shell prompts"
conda config --set env_prompt '({name})'

# add env to config (env is now found by --name, -n)
echo "Adding env to config"
conda config --append envs_dirs ./env/

# activate the environemnt
echo "Activating the environment"
conda activate $ENV_NAME

#conda clean -a -y

conda env update -f env.yml --prune