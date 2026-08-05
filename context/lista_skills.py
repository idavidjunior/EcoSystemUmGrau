# Lista dos dominios tecnicos do plano sem skill correspondente.
# Formato: (id, dominio_mcp, titulo, descricao, triggers)
SKILLS = [
    # --- IA/MLOps ---
    ("prompt-engineering", "desenvolvimento", "Prompt Engineering",
     "Engenharia de prompts para LLMs: design de instrucoes, few-shot, chain-of-thought, contexto, formatos de saida e otimizacao de resultados. Trigger: prompt, instrucao, few-shot, chain-of-thought, system prompt, engenharia de prompt."),
    ("rag-implementation", "desenvolvimento", "RAG Implementation",
     "Implementacao de Retrieval-Augmented Generation: indexacao, chunks, recuperacao, rerank, injecao de contexto e citacao de fontes. Trigger: RAG, retrieval-augmented, injetar contexto, recuperacao, chunks, rerank."),
    ("fine-tuning", "desenvolvimento", "Fine-Tuning",
     "Ajuste fino de modelos de linguagem: preparacao de dataset, hyperparametros, LoRA/QLoRA, avaliacao de perda de capacidade. Trigger: fine-tune, fine-tuning, LoRA, QLoRA, ajustar modelo, dataset de treino."),
    ("eval-testing", "desenvolvimento", "Eval & Testing de LLM",
     "Avaliacao de modelos e pipelines de IA: metrivas, benchmarks, testes de regressao de qualidade, golden sets. Trigger: eval, avaliar modelo, benchmark, golden set, metrica de qualidade, regressao de IA."),
    ("agent-orchestration", "desenvolvimento", "Agent Orchestration",
     "Orquestracao de agentes de IA: planejamento, execucao paralela, memoria entre passos, ferramentas, loops autonomos e composicao. Trigger: orquestrar agentes, multi-agente, planner, loop autonomo, coordenador de agentes."),
    ("mlops", "desenvolvimento", "MLOps",
     "Operacoes de machine learning: pipelines de treino, versionamento de modelos, registro, deploy, monitoramento e reproducibilidade. Trigger: MLOps, pipeline de ML, versionar modelo, deploy de modelo, reproducibilidade, registro de modelo."),
    ("vector-databases", "desenvolvimento", "Vector Databases",
     "Bancos vetoriais para busca semantica: embeddings, indice ANN, distancia, filtros, escalabilidade e hibridos. Trigger: vector database, banco vetorial, embeddings, indice ANN, busca por similaridade, faiss, milvus, qdrant, pgvector."),

    # --- DevOps/Infra ---
    ("kubernetes", "desenvolvimento", "Kubernetes",
     "Orquestracao de containers: pods, deployments, services, ingress, configmaps, secrets, health probes, scaling e operacao. Trigger: kubernetes, k8s, pod, deployment, service, ingress, helm, kubectl."),
    ("terraform", "desenvolvimento", "Terraform",
     "Infraestrutura como codigo com Terraform: HCL, providers, state, modules, plan/apply, drift e boas praticas. Trigger: terraform, HCL, infra-as-code, state, provider, module, apply, plan."),
    ("ci-cd-pipeline", "desenvolvimento", "CI/CD Pipeline",
     "Pipelines de integracao e entrega continua: build, teste, artefato, deploy, estrategias de release e gatilhos. Trigger: CI/CD, pipeline, integracao continua, entrega continua, build, release, github actions, jenkins."),
    ("infrastructure-as-code", "desenvolvimento", "Infrastructure as Code",
     "Infraestrutura como codigo: declarativa vs imperativa, configuracoes versionadas, reproducibilidade e pratica de gerenciamento. Trigger: IaC, infra como codigo, reproducibilidade, config versionada, declarativo."),
    ("monitoring-alerting", "desenvolvimento", "Monitoring & Alerting",
     "Monitoramento e alertas: metricas, logs, traces, dashboards, SLO/SLI, alertas com acao e on-call. Trigger: monitoramento, alertas, metricas, SLO, dashboards, on-call, prometheus, grafana, logs."),
    ("service-mesh", "desenvolvimento", "Service Mesh",
     "Service mesh: proxy sidecar, mTLS, observabilidade de rede, retries/timeouts e controle de trafego entre servicos. Trigger: service mesh, sidecar, mTLS, istio, linkerd, trafego, malha de servicos."),

    # --- Seguranca ---
    ("threat-modeling", "desenvolvimento", "Threat Modeling",
     "Modelagem de ameacas: identificar ativos, adversarios, superficies de ataque e mitigacoes (STRIDE). Trigger: threat modeling, modelagem de ameaca, STRIDE, adversario, superficie de ataque, DREAD."),
    ("secure-coding", "desenvolvimento", "Secure Coding",
     "Codigo seguro: prevencao de injecao, XSS, CSRF, SSRF, vazamento de segredos e boas praticas por linguagem. Trigger: codigo seguro, secure coding, injecao, XSS, CSRF, SSRF, vazamento de segredo, OWASP."),
    ("vulnerability-scanning", "desenvolvimento", "Vulnerability Scanning",
     "Escaneamento de vulnerabilidades: dependencias, codigo, container, surface scan e priorizacao de remediacao. Trigger: vulnerabilidade, scan, CVE, dependencia, SAST, DAST, priorizar fix, SBOM."),
    ("compliance-audit", "desenvolvimento", "Compliance & Audit",
     "Conformidade e auditoria: LGPD/GDPR, trilhas de auditoria, retencao, provas de conformidade e revisoes. Trigger: compliance, LGPD, GDPR, auditoria, trilha de auditoria, retencao, conformidade."),

    # --- Arquitetura ---
    ("domain-driven-design", "desenvolvimento", "Domain-Driven Design",
     "Modelagem orientada a dominio: bounded contexts, entities, value objects, aggregates, ubiquitous language e eventos de dominio. Trigger: DDD, domain-driven, bounded context, agregado, value object, ubiquitous language."),
    ("event-sourcing", "desenvolvimento", "Event Sourcing",
     "Armazenamento de estado como sequencia de eventos: append-only, replay, projecoes e consistencia eventual. Trigger: event sourcing, eventos de dominio, replay, projecoes, append-only, event store."),
    ("cqrs", "desenvolvimento", "CQRS",
     "Command Query Responsibility Segregation: separacao de leitura/escrita, otimizacao de leituras, consistencia e escalabilidade. Trigger: CQRS, command, query, segregacao leitura escrita, modelos de leitura, modelos de escrita."),
    ("microservices-patterns", "desenvolvimento", "Microservices Patterns",
     "Padroes de microservicos: API gateway, service discovery, circuit breaker, saga, outbox, decomposicao e comunicacao. Trigger: microservicos, microservices, API gateway, circuit breaker, saga, outbox, service discovery."),

    # --- Mobile ---
    ("ios", "android", "iOS Development",
     "Desenvolvimento iOS nativo: Swift, SwiftUI, UIKit, ciclo de vida, Xcode, App Store e integracoes. Trigger: iOS, Swift, SwiftUI, UIKit, Xcode, app store, iphone, ipad."),
    ("flutter", "android", "Flutter",
     "Desenvolvimento multiplataforma com Flutter: Dart, widgets, estado, build para Android/iOS/web e perfomance. Trigger: flutter, Dart, widgets, cross-platform, multiplataforma, riverpod, bloc."),
    ("react-native", "android", "React Native",
     "Desenvolvimento multiplataforma com React Native: componentes nativos, bridge, estado, performance e native modules. Trigger: react native, RN, bridge, componente nativo, multiplataforma, native module."),
    ("expo", "android", "Expo",
     "Desenvolvimento com Expo: managed workflow, EAS Build, over-the-air updates, dev client e servicos Expo. Trigger: expo, EAS, over-the-air, OTA, dev client, managed workflow, expo go."),

    # --- Frontend ---
    ("react-vue-svelte-patterns", "desenvolvimento", "React/Vue/Svelte Patterns",
     "Padroes de frameworks frontend: componentes, hooks, composables, stores, renderizacao, otimizacao e arquitetura de UI. Trigger: react, vue, svelte, hooks, composables, components, stores, VDOM, frontend patterns."),
    ("state-management", "desenvolvimento", "State Management",
     "Gerenciamento de estado frontend: global vs local, stores, derivacao, memoizacao, cache e escalabilidade. Trigger: state management, gerenciamento de estado, store, redux, zustand, pinia, signal, memoizacao."),
    ("css-architecture", "desenvolvimento", "CSS Architecture",
     "Arquitetura de CSS: BEM, CSS-in-JS, design tokens, nomes, especificidade, layout e manutencao. Trigger: CSS architecture, BEM, design tokens, css-in-js, tailwind, especificidade, layout, estilos escalaveis."),
    ("accessibility", "desenvolvimento", "Accessibility",
     "Acessibilidade (a11y): ARIA, semantica, teclado, contraste, foco, screen readers e WCAG. Trigger: acessibilidade, accessibility, a11y, ARIA, WCAG, screen reader, teclado, contraste, foco."),

    # --- Backend ---
    ("graphql", "desenvolvimento", "GraphQL",
     "APIs GraphQL: schema, resolvers, queries/mutations/subscriptions, federation, caching e boas praticas. Trigger: graphql, schema, resolver, query, mutation, subscription, federation, apollo."),
    ("grpc", "desenvolvimento", "gRPC",
     "Comunicacao RPC com gRPC: protobuf, streams, interceptors, deadline, load balancing e performance. Trigger: gRPC, protobuf, RPC, stream, interceptor, deadline, bidirecional."),
    ("message-queues", "desenvolvimento", "Message Queues",
     "Filas de mensagens: broker, producer/consumer, dead letter, delivery garanties, padroes e monitoramento. Trigger: fila, queue, message broker, rabbitmq, kafka, pub-sub, dead letter, consumer."),
    ("event-driven-architecture", "desenvolvimento", "Event-Driven Architecture",
     "Arquitetura dirigida a eventos: eventos de dominio, streams, consumidores, saga, idempotencia e consistencia. Trigger: event-driven, arquitetura de eventos, streams, consumidor, saga, idempotencia, pub-sub."),

    # --- Engenharia de Dados ---
    ("data-pipeline", "desenvolvimento", "Data Pipeline",
     "Pipelines de dados: extracao, transformacao, carga (ETL/ELT), agendamento, qualidade e monitoramento. Trigger: data pipeline, ETL, ELT, extracao, transformacao, carga, airflow, dbt, qualidade de dados."),
    ("feature-engineering", "desenvolvimento", "Feature Engineering",
     "Engenharia de atributos: criacao, transformacao, normalizacao, selecao e tratamento de dados para modelos. Trigger: feature engineering, engenharia de atributos, normalizacao, selecao de features, transformacao."),
    ("model-training", "desenvolvimento", "Model Training",
     "Treinamento de modelos de ML: divisao de dados, hiperparametros, overfitting, validacao cruzada e reproducibilidade. Trigger: treinar modelo, model training, hiperparametros, overfitting, validacao cruzada, split de dados."),
    ("database-design", "desenvolvimento", "Database Design",
     "Modelagem de banco de dados: normalizacao, esquema, indices, relacoes, migracoes e desempenho. Trigger: database design, modelagem, normalizacao, esquema, indice, relacao, migracao, DDL."),
    ("nosql-patterns", "desenvolvimento", "NoSQL Patterns",
     "Padroes NoSQL: document, key-value, columnar, graph; modelagem por consulta, eventual consistency e trade-offs. Trigger: nosql, document, mongodb, redis, dynamodb, columnar, cassandra, graph database, eventual consistency."),

    # --- Qualidade ---
    ("code-review", "desenvolvimento", "Code Review",
     "Revisao de codigo: checklist, critica construtiva, aprovacao, bloqueadores e eficiencia do processo. Trigger: code review, revisar codigo, checklist de revisao, aprovacao, bloqueador, pull request."),
    ("refactoring-patterns", "desenvolvimento", "Refactoring Patterns",
     "Refatoracao: tecnica de melhoria de codigo sem mudar comportamento, com testes de seguranca e passos pequenos. Trigger: refatorar, refactoring, tecnica, extrair metodo, renomear, testes de seguranca, code smell."),
    ("legacy-modernization", "desenvolvimento", "Legacy Modernization",
     "Modernizacao de sistemas legados: estrtatira, modulo a modulo, estrangulamento, lift-and-shift e migracao segura. Trigger: legacy, legado, modernizacao, estrangulamento, strangler fig, migracao, lift-and-shift."),
    ("technical-debt", "desenvolvimento", "Technical Debt",
     "Divida tecnica: identificacao, triagem, custo, plano de pagamento e governanca. Trigger: divida tecnica, technical debt, triagem, custo, pagamento, refatorar, quadro."),
    ("contract-testing", "desenvolvimento", "Contract Testing",
     "Teste de contratos: pacto entre consumidor/produtor, schemas, compatibilidade e regressao de APIs. Trigger: contract testing, teste de contrato, pact, consumer-driven, schema, compatibilidade, API contract."),
    ("performance-testing", "desenvolvimento", "Performance Testing",
     "Teste de performance: load, stress, endurance, pico, metricas e otimizacao. Trigger: performance testing, load test, stress test, teste de carga, endurance, pico, latencia, throughput."),

    # --- Documentacao ---
    ("technical-writing", "desenvolvimento", "Technical Writing",
     "Escrita tecnica: documentacao de codigo, estrutura, clareza, exemplos e manutencao. Trigger: documentacao, technical writing, escrita tecnica, guia, manual, README, clarity, exemplos."),
    ("api-documentation", "desenvolvimento", "API Documentation",
     "Documentacao de APIs: OpenAPI/Swagger, exemplos, schemas, versionamento e experienca do consumidor. Trigger: API docs, documentacao de API, OpenAPI, Swagger, schema, endpoints, versionar API."),
    ("adr", "desenvolvimento", "ADR (Architecture Decision Records)",
     "Registros de decisoes de arquitetura: contexto, decisao, consequencias, formato e manutencao do registro. Trigger: ADR, architecture decision record, registro de decisao, contexto, consequencia, Nygard."),
    ("runbooks", "desenvolvimento", "Runbooks",
     "Runbooks operacionais: procedimentos de incidente, checklist, recuperacao, escalacao e padronizacao. Trigger: runbook, procedimento, incidente, recuperacao, checklist, escalacao, playbook, O&M."),
]
