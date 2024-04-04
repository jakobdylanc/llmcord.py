#!/bin/bash

ENV_FILE=".env"
while IFS='=' read -r name value ; do
    if [[ "$name" =~ ^(PATH|PWD|SHLVL|_) ]]; then
        continue
    fi

    sed -i "/^$name=/d" "$ENV_FILE"
    echo "$name=$value" >> "$ENV_FILE"
done < <(env)

python llmcord.py
