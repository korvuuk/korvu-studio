# Calendário de publicação

O agente `publicador` usa este arquivo para agendar. Edite as vagas à vontade.
(Fixture dos testes: as vagas abaixo são as que `test_publicar.py` espera — quarta e sexta às 19:00.)

```yaml
fuso: Europe/London
vagas_semanais:        # dia: hora (24h)
  segunda: "19:00"
  quarta: "19:00"
  sexta: "19:00"
plataformas_padrao: [instagram, facebook]
trial_padrao:
modo_confirmar_restantes: 2   # os primeiros N posts pedem OK antes de publicar
```

## Agenda
| Data/hora | Slug | Plataformas | Estado |
|---|---|---|---|
