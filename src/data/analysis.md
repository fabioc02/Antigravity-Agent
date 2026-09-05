# Análise Técnica: Agente de Desenvolvimento Autônomo (Qwen + Colab)

A arquitetura proposta descreve um sistema avançado e robusto, superando um simples "wrapper" de LLM para se tornar um verdadeiro engenheiro de software autônomo. Abaixo detalho a análise técnica, tecnologias recomendadas e o plano de ação por fases.

## 1. Arquitetura de Hardware e Modelos (Colab & Qwen)
O Google Colab oferece acesso gratuito/pago a GPUs T4 (16GB VRAM), V100 (16GB) ou A100 (40GB).
* **O Desafio:** Modelos de ponta em codificação (como Qwen 2.5 Coder 32B) não cabem em 16GB VRAM em precisão FP16 (precisariam de ~64GB).
* **A Solução:** Utilizar **Qwen2.5-Coder-7B-Instruct** (em FP16 ou AWQ 4-bit) ou **Qwen2.5-Coder-32B-Instruct-AWQ** (se utilizarmos offload de CPU inteligente via biblioteca `llama.cpp` ou `vLLM`).
* **Inferência:** Recomendo o uso do framework **vLLM** ou **llama.cpp** no Colab para máxima velocidade de inferência e suporte nativo a *Tool Calling* (Function Calling).

## 2. Persistência (Google Drive vs. Workspace)
A abordagem sugerida é arquitetonicamente correta:
* **Drive (`/content/drive/MyDrive/AI_AGENT/`)**: Extremamente lento para milhares de leituras/escritas simultâneas (o que destruiria o tempo de um `npm install` ou `./gradlew build`).
* **Workspace (`/content/workspace/`)**: Armazenamento local rápido (SSD) da instância do Colab.
* **Mecanismo:** O Agente faz `rsync` ou cópia via scripts do Drive para o Workspace ao iniciar a sessão, trabalha localmente e sincroniza o `.ai/SESSION.md`, commits e artefatos de volta para o Drive ao finalizar ou fazer checkpoints.

## 3. O "Cérebro" Autônomo e Tool Calling
O loop cognitivo do agente deve seguir o padrão ReAct (Reason + Act):
1. **System Prompt** define as ferramentas disponíveis em formato JSON Schema.
2. Agente responde com um JSON contendo `{"thought": "...", "action": "...", "action_input": {...}}`.
3. O parser intercepta, executa a função Python real, e devolve a `Observation`.
4. Ciclo se repete até a ação `Finish`.

## 4. O Local Agent Bridge (Segurança e Conectividade)
Para o Colab controlar o PC do usuário:
* O PC local roda um servidor Node.js/Python (Local Bridge).
* O PC local expõe a conexão via **ngrok**, **Cloudflare Tunnels**, ou **WebSockets** (conectando-se a um relay).
* **Segurança:** O Bridge terá um `config.yaml` implementando `chroot` virtual (restringindo caminhos) e interceptando comandos destrutivos via Regex e AST parsing.

## 5. Gerenciamento de Memória (`.ai/`)
A criação do diretório `.ai/` dentro de cada projeto é fundamental para recuperar o estado. Ele servirá como a "memória de longo prazo" (RAG simples baseado em arquivos) do projeto.

---

## 📅 Plano de Implementação (Fases)

### FASE 1: Fundação do Sistema (Implementando agora)
- Setup da arquitetura de diretórios do Agente Python (`qwen-agent-colab/`).
- Construção da Interface Web de Gerenciamento (este Dashboard).
- Configuração do **Local Agent Bridge** (servidor Node.js mock/base para gerenciar segurança e rotas).
- Validação: O Dashboard consegue listar projetos e o Bridge inicializa com whitelists.

### FASE 2: Cérebro Autônomo (Python Core)
- Implementação do `agent.py` e abstração do provedor LLM.
- Definição do loop ReAct (Task -> Inspect -> Plan -> Edit).
- Validação: Loop consegue processar uma simulação de "thought & action".

### FASE 3: Ferramentas de Sistema (Tools)
- Implementação de `filesystem.py`, `terminal.py`, `memory.py`.
- Lógica de compilação C++/Java/Android e análise de log (Regex para stderr).

### FASE 4: Integração Colab & Persistência
- Scripts de montagem do Drive (`setup_colab.ipynb`).
- Sincronização Workspace <-> Drive.

### FASE 5 & 6: Git, Github, APIs e Polimento
- Ferramentas de diff e controle de source.
- Controle de limites (max_iterations, tempo de comando).

*A arquitetura inicial (Fase 1) será estruturada a seguir nos arquivos do projeto.*
