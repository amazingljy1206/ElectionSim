#!/bin/bash


user_profile_folder="users/2024_1000" # user profile
output_path="output/2024_1000"
pattern="2024"
model="qwen"
baseline="31"
num_threads="64"
poll_path="polls/2024/poll_vote.json" # voting res
# allowed_states=("Georgia" "Iowa" "West_Virginia" "Wyoming" "South_Dakota" "North_Carolina") # "ALL" or list
allowed_states="ALL"

for file in $(ls $user_profile_folder | grep ".json$"); do
    state_name=$(echo $file | cut -d'.' -f1)
    if [[ "$allowed_states" != "ALL" && ! " ${allowed_states[@]} " =~ " ${state_name} " ]]; then
        continue
    fi

    python sim.py --poll_path "${poll_path}" --baseline "${baseline}" --pattern "${pattern}" --state_name "${state_name}" --user_profile_folder "${user_profile_folder}" --output_path "${output_path}" --model "${model}" --num_threads "${num_threads}"
done