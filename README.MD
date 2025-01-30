## install ollama
windows: download the app
mac: brew

## run ollama
ollama serve

## work with models
to pull a model: ollama pull deepseek-r1:1.5b(any model from ollama can be pulled)
to execute a mode: ollama run model(ex ollama run deepseek-r1:1.5b )

## download and execute open web ui and connect with your local ollama server:
docker run -d -p 3000:8080 --add-host=host.docker.internal:host-gateway -v open-webui:/app/backend/data --name open-webui --restart always ghcr.io/open-webui/open-webui:main 

## ollama on docker
to run both ollama and web ui in docker use my docker compose
docker compose up -d

## interact with ollama in docker:
docker exec -it ollama bash
## install a model and run it:
ollama pull mistral
ollama run mistral

## call the ollama srver with a model using http:
 curl -X POST http://localhost:11434/api/generate -d '{
  "model": "mistral",
  "prompt": "What is the best way to learn Python?",
  "stream": false
}' -H "Content-Type: application/json"