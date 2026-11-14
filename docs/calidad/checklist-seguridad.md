# Checklist de seguridad (WBS 4.4)

**Fecha de revisión:** 14-nov-2026, sobre `main` ya desplegado en Railway (T24), con la E2E (T25) y el límite de intentos de Django Admin (T33).
**Referencia:** OWASP Top 10:2021. **Alcance:** la aplicación Django, el cliente sin red de `static/pos/` y la configuración de producción.

Las pruebas se citan como en la matriz de trazabilidad, [apéndice B del SRS](../SRS.md#apéndice-b-matriz-de-trazabilidad-wbs-43) (`acc` = `apps/accounts/tests.py`, `pos-v` = `apps/pos/tests_views.py`, etc.).

Estados: ✅ cumple · ⚠ cumple con un riesgo aceptado o una mejora pendiente.

## 1. Lo que pide la WBS 4.4

| # | Control | Estado | Evidencia |
|---|---|---|---|
| 1 | Contraseñas y PIN guardados con hash | ✅ | El PIN es la contraseña de la cuenta y Django lo guarda con su hasher (`check_password`). `acc` UserModelTests.test_password_is_hashed, AdminPinTests.test_pin_is_the_password |
| 2 | El dispositivo nunca guarda el PIN | ✅ | Solo un verificador PBKDF2-SHA256 de 600 000 iteraciones, con sal por usuario, que caduca a los 7 días sin sincronizar. `acc` AdminPinTests.test_verifier_never_contains_the_pin, .test_same_pin_gets_a_different_salt_per_user · `node` test_pin_verifier |
| 3 | Límite de intentos del PIN en la aplicación | ✅ | 5 fallos seguidos bloquean el PIN 15 minutos, también con el PIN correcto y aunque se borre la cookie (el contador vive en la caché de la base de datos). `acc` VerifyAdminPinTests.test_five_failures_lock_the_pin_even_for_the_right_one · `acc-v` ActivateDeviceViewTests.test_five_failures_lock_even_with_a_new_cookie |
| 4 | Límite de intentos en Django Admin | ✅ | Su contraseña es el mismo PIN (DEC-38), así que `/admin/login/` comparte el contador: 5 fallos bloquean los dos 15 minutos y un acierto lo reinicia. `acc` AdminLoginLimitTests |
| 5 | CSRF activo | ✅ | `CsrfViewMiddleware` en todas las vistas y ninguna con `csrf_exempt`. HTMX manda el token en `hx-headers`, y `db.js` lo lee de la cookie para `/pos/sync/` (por eso `CSRF_COOKIE_HTTPONLY = False`, intencional). `pos` SyncOperationsTests.test_needs_the_csrf_token |
| 6 | Autorización en el servidor, en cada vista | ✅ | Mixins de `apps/core/mixins.py`; ocultar un botón no es el control. `core` RoleRequiredTests, AdminPinRequiredTests · `cat-v`, `inv-v` y `rep-v` AccessTests |
| 7 | Rol revalidado en las operaciones sincronizadas | ✅ | Una venta o apertura de un usuario que ya no tiene el rol va a cuarentena (`usuario_sin_permiso`), nunca se aplica. `pos` SaleServiceTests.test_user_without_permission, SyncOperationsTests.test_quarantine_reasons |
| 8 | Secretos fuera del repositorio | ✅ | `.env` en `.gitignore`; `DJANGO_SECRET_KEY` y `DATABASE_URL` son obligatorias y salen del entorno; el CI usa valores de prueba no secretos. Ningún archivo de credenciales en `git ls-files`. |

## 2. OWASP Top 10:2021

| Riesgo | Estado | Qué hay |
|---|---|---|
| **A01** Control de acceso roto | ✅ | Dos roles; lo restringido pide el PIN de Administrador y caduca a los 30 minutos (`core` UnlockTests.test_unlock_lasts_thirty_minutes). Un Administrador desactivado o degradado pierde el desbloqueo (.test_unlock_by_deactivated_or_demoted_admin_does_not_count). Django Admin solo para `is_staff` (`acc` AccessRestrictionTest). |
| **A02** Fallas criptográficas | ⚠ | En producción: cookies de sesión y CSRF con `Secure`, y `SECURE_PROXY_SSL_HEADER` para Railway. **Riesgo aceptado (DEC-28):** el verificador sin red de un PIN de 6 dígitos se puede romper por fuerza bruta si alguien copia la base local del iPhone; por eso caduca a los 7 días y la cuenta sigue protegida en el servidor. HSTS con `DJANGO_SECURE_HSTS_SECONDS`: 3600 mientras se valida en el iPhone (T30); después sube a un año (31536000). `includeSubDomains` y `preload` se silencian a propósito (W005, W021): el dominio es un subdominio de `railway.app`, que no es nuestro. |
| **A03** Inyección | ✅ | Solo el ORM: ni `raw()`, ni `extra()`, ni `cursor()`. Las plantillas escapan todo: no hay `\|safe` ni `mark_safe`, y los datos sin red van con `json_script`. |
| **A04** Diseño inseguro | ✅ | Reglas del cliente en el servidor: el total se recalcula y lo que no cuadra va a cuarentena (regla 14); la unicidad del UUID es una restricción de la base de datos (regla 8); el cierre se niega con pendientes (regla 5). |
| **A05** Configuración incorrecta | ✅ | `DEBUG` es `False` si no se indica otra cosa; `ALLOWED_HOSTS` y `CSRF_TRUSTED_ORIGINS` salen del entorno; `XFrameOptionsMiddleware` activo. En Railway, `DJANGO_SECURE_SSL_REDIRECT=True` manda todo a HTTPS. Los errores salen por stdout a los registros de Railway, sin mostrarse al usuario. |
| **A06** Componentes vulnerables | ✅ | Versiones fijas en `requirements.txt` (Django 5.2 LTS) y en las URL de los CDN (HTMX 2.0.4, Alpine 3.14.8, Dexie 4.0.10, Workbox 7.3.0). |
| **A07** Fallas de identificación y autenticación | ✅ | PIN de 6 dígitos con `CommonPasswordValidator`, y el mismo límite de intentos en la aplicación y en Django Admin (controles 3 y 4). La sesión del dispositivo dura un año por diseño (DEC-34): si se pierde el iPhone, el Administrador desactiva la cuenta de cajero en Django Admin y la sesión deja de servir (`core` RoleRequiredTests.test_inactive_user_is_rejected). |
| **A08** Integridad de software y datos | ⚠ | La venta no se reescribe: es inmutable y se corrige con ajustes que dejan rastro (regla 7). **Mejora:** los scripts de CDN no llevan `integrity` (SRI); una versión fija reduce el riesgo pero no lo elimina. |
| **A09** Registro y monitoreo | ⚠ | Quedan registrados quién abrió y cerró cada turno, quién autorizó cada ajuste, la cuarentena con su JSON original y quién la resolvió, y las ventas marcadas para revisión. **Mejora:** los intentos fallidos del PIN se cuentan pero no se escriben en un log. |
| **A10** SSRF | ✅ | El servidor no hace peticiones a URL que vengan del usuario. |

## 3. Datos personales (LFPDPPP)

✅ Solo se guardan datos del personal (nombre, rol y credenciales). El comensal no tiene cuenta ni datos. Las cuentas se desactivan, nunca se borran, y nunca se puede desactivar al último Administrador activo (`acc` DeactivateUserTests). La demo usa datos ficticios (fixture `apps/catalog/fixtures/demo.json`).

## 4. Despliegue

- [ ] En Railway: `DJANGO_DEBUG=False`, una `DJANGO_SECRET_KEY` nueva, `DJANGO_ALLOWED_HOSTS` y `DJANGO_CSRF_TRUSTED_ORIGINS` con el dominio, `DJANGO_SECURE_SSL_REDIRECT=True` y `DJANGO_SECURE_HSTS_SECONDS` (T24).
- [ ] Cinco PIN incorrectos en `/admin/login/` de producción lo bloquean 15 minutos (T33).
- [ ] Tras validar en el iPhone (T30), `DJANGO_SECURE_HSTS_SECONDS=31536000`.
- [ ] `python manage.py check --deploy` sin avisos con las variables de producción.

**Revisó:** Jesús Hernández · **Aprobó:** Alejandro Tarín
