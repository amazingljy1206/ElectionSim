export CUDA_VISIBLE_DEVICES=0,1,2,3
python -m vllm.entrypoints.openai.api_server \
    --model /fdudata/jylin/models/Qwen2.5-72B-Instruct \
    --served_model_name qwen2.5-72b \
    --tensor-parallel-size 4 \
    --max-model-len 4096 \
    --enable-prefix-caching \
    --enforce-eager \
    --host 0.0.0.0 \
    --port 1357