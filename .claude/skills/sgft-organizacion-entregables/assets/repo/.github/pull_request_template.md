## Qué cambia

<!-- Una o dos líneas. -->

<!-- Título del PR: WBS-x.y.z: descripción (DEC-23). Rama: nombre/tema. -->
**Paquete WBS:** WBS-x.y.z

Closes #<!-- número del Issue -->

## Checklist del autor (organización SGFT — ver docs/decisiones/organizacion-repositorio.md)

- [ ] Cada archivo está en la ruta que indica el mapa de propiedad: `git diff --name-only --diff-filter=d origin/main...HEAD | python .claude/skills/sgft-organizacion-entregables/scripts/dueno_de_ruta.py --revisar` no muestra bloqueos.
- [ ] Si toqué una función que vive en un archivo ajeno, su autor y el dueño del archivo están como revisores.
- [ ] Si toqué `models.py`, avisé antes a Jesús, la migración va en esta rama y es nueva (no edita ni borra una aplicada), y mencioné a Jesús abajo para avisarle (DEC-37, DEC-39).
- [ ] Toda vista nueva tiene su contrato vista–plantilla en el docstring y el dueño de la plantilla lo aprobó.
- [ ] Los fragmentos HTMX están en `partials/`; ninguna plantilla ni código Alpine calcula dinero o decide reglas.
- [ ] Si toqué `static/pos/`, hubo pareja y ambos aparecen como autores (`Co-authored-by:` en el commit).
- [ ] Si toqué `services_pricing.py` o `pricing.js`, cambié los dos y `tests_fixtures/pricing_cases.json`, y `node --test` pasa.
- [ ] Si toqué `db.js` o `sync_operations()`, el cambio respeta `docs/decisiones/contrato-sync-pdv.md` (o sube su versión con aprobación de Jesús, Jared y Tarín).
- [ ] Las pruebas del servicio que implementé están en el `tests.py` de su app y `python manage.py test` pasa.
- [ ] No hay credenciales, `.env` ni datos reales del negocio (el repositorio es público).
- [ ] Si el código se apartó del SRS, actualicé `docs/SRS.md` en este mismo PR.

## Dueños a los que conviene avisar

<!-- Menciona al dueño de cada archivo que tocaste según el mapa de propiedad, para avisarle (solo Tarín aprueba, DEC-39). P. ej. "@EduardGarrido: toca deduct_for_sale()". -->

## Para el integrador (Tarín) — antes de aprobar y fusionar

- [ ] La revisión de rutas (`--revisar` o el job de CI) no tiene bloqueos: nada "fuera de la estructura" ni "en evaluación".
- [ ] Los avisos están atendidos: coautoría en `static/pos/` y visto bueno del autor si se tocó una función ajena.
- [ ] Revisé el contenido. Si toca `models.py`, `migrations/`, servicios transaccionales o la sincronización, avisé a Jesús (DEC-39).
- [ ] El PR está ligado a su Issue (`Closes #n`).
- [ ] CI en verde (`manage.py test`, `node --test`, revisión de rutas).
