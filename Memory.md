# Memory.md — legislacion_monitor
> Ultima actualizacion: 2026-04-27

## Estado actual

- **Fase**: Revisado, correcciones criticas aplicadas
- **Ultimo cambio significativo**: SECRET_KEY, 127.0.0.1, pip auto-install eliminado (2026-04-27)
- **Tamano**: 968 KB, 39 archivos (Python/HTML/Docs)

## Infraestructura

| Elemento | Estado | Detalle |
|----------|--------|---------|
| Git | Si | Inicializado 2026-04-26 |
| GitHub | **No** | Pendiente de crear repo y subir |
| SonarCloud | **No** | Pendiente de conectar |
| .gitignore | Si | Creado 2026-04-26 |
| AGENTS.md | Si | Ya existe |
| Memory.md | Si | Este archivo |

## Historial de decisiones

| Fecha | Decision | Razon |
|-------|----------|-------|
| 2026-04-26 | Proyecto movido a ~/Proyectos/ | Centralizacion fuera de iCloud |
| 2026-04-26 | Git inicializado con .gitignore | Versionado de todos los proyectos |

## Revisiones de calidad/seguridad

| Fecha | Tipo | Resultado |
|-------|------|-----------|
| 2026-04-27 | Revision manual (OpenCode) | 4 criticos + 5 altos + 4 medios (seguridad), 6 altos + 8 medios + 4 bajos (calidad) |

### Correcciones aplicadas (2026-04-27)
1. Flask SECRET_KEY generada con os.urandom() (ALTO)
2. Servidor cambiado de 0.0.0.0 a 127.0.0.1 (ALTO)
3. pip auto-install eliminado en export_excel.py — ahora lanza ImportError claro (ALTO)

### Pendiente de corregir
- **CRITICO**: XSS en emails (src/notifier.py) — campos sin html.escape()
- **CRITICO**: XSS en ejecutar.html (innerHTML con data.reason sin sanitizar)
- **ALTO**: Sin CSRF en POST /ejecutar
- **ALTO**: Endpoint /exportar sin autenticacion
- **MEDIO**: SSRF potencial en URLs de config.yaml

## Pendiente

- [x] ~~Revision de calidad y seguridad~~ (completada 2026-04-27)
- [x] ~~SECRET_KEY + 127.0.0.1 + pip auto-install~~ (aplicado 2026-04-27)
- [ ] Sanitizar HTML en emails del notifier (html.escape)
- [ ] Sanitizar innerHTML en ejecutar.html (usar textContent)
- [ ] Anadir CSRF al POST /ejecutar
- [ ] Anadir autenticacion basica a /exportar
- [ ] Ampliar cobertura de tests
- [ ] Crear repo en GitHub y subir
- [ ] Conectar a SonarCloud

## Notas y descubrimientos

- Monitor de legislacion: seguimiento de cambios normativos relevantes para consultoria.
- Contiene codigo Python y HTML.

---

> **Revisado 2026-11-13** — sin cambios de código en esta sesión (trabajo centrado en `Plataforma_Seguimiento_Proyectos`).
