
#### `TODO.md`

Список задач для развития проекта.

```markdown
# SafeVault TODO List

## Phase 1: MVP Core (Current)
- [x] Project Structure Setup
- [x] Database Connection (Motor)
- [x] Crypto Service Implementation (Envelope Encryption)
- [ ] Implement Project CRUD API
    - [ ] Create Project (generate keys)
    - [ ] List Projects
    - [ ] Delete Project
- [ ] Implement Secret CRUD API
    - [ ] Create Secret (encrypt using project key)
    - [ ] Get Secret (decrypt)
    - [ ] Update Secret
    - [ ] Delete Secret

## Phase 2: Usability
- [ ] Basic CLI Client (Python script to fetch secrets)
- [ ] Web UI (Simple HTML/JS or Jinja2 templates)
- [ ] Docker Healthchecks
- [ ] Error Handling & Validation

## Phase 3: Advanced Features
- [ ] LLM Integration (AI Assistant for config generation)
- [ ] User Authentication (Basic Auth or JWT)
- [ ] Audit Logs (who accessed which secret)
- [ ] Secret Rotation logic

## Phase 4: Production Ready
- [ ] HTTPS (Nginx/Traefik integration)
- [ ] Backup & Restore scripts
- [ ] Performance Testing
