# Infraestrutura, Implantação e Rollback

## Infraestrutura Existente

**Deployment actual:** execução local por Node e frontend estático servido pelo Express.

**Ferramentas:** npm scripts, Docker Compose para Evolution API, ficheiros `.env`.

**Ambientes:** local. Não há evidência de cloud, CI/CD remoto ou ambiente de produção formal.

## Estratégia de Deployment da Melhoria

- Executar Node legado e Python em portas locais distintas durante transição: Node em `3000`, Python em `8000`.
- Manter Evolution API por Docker Compose existente.
- Documentar variáveis Python em `.env.example` quando o backend for criado.
- Usar SQLite em `data/app.sqlite3` e backups locais antes de migração/importação.
- Só encaminhar UI existente para endpoints Python quando a story correspondente tiver testes e checklist concluídos.

## Rollback

- **Código:** rollback por reversão da story/branch, sem apagar dados gerados.
- **DB:** antes de migrações ou importações, copiar `data/app.sqlite3` para `data/legacy-backups/` com timestamp.
- **JSON:** nunca remover ficheiros JSON no mesmo passo que introduz DB.
- **Fluxo MVP:** se a API Python falhar, o Node legado continua a permitir fluxo crítico enquanto os ficheiros JSON estiverem íntegros.
- **Broadcast:** usar `dry_run` e contagens antes de envio real; entregas parciais devem ser reconciliadas por `notification_deliveries`.
