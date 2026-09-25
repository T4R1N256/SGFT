# Guía: acceso al repositorio y ambiente de desarrollo del SGFT

Esta guía te lleva desde cero hasta tener el proyecto corriendo en tu computadora, con las pruebas en verde y listo para abrir tu primer Pull Request. Asume que el esqueleto de Django (paquete 3.1.1) ya está fusionado en `main`.

**Al terminar tendrás:**

- acceso de escritura al repositorio;
- el proyecto clonado;
- Python con sus dependencias en un entorno virtual;
- tu propio `.env`;
- una base de datos PostgreSQL local;
- `python manage.py test` en verde;
- el sitio abriendo en `http://127.0.0.1:8000/admin/`.

Tiempo estimado: 30 a 45 minutos la primera vez.

## Contenido

1. Acceso a GitHub
2. Herramientas (según tu sistema operativo)
3. Clonar el repositorio
4. Entorno virtual y dependencias
5. Archivo `.env`
6. Base de datos PostgreSQL
7. Inicializar y comprobar el proyecto
8. Claude y la skill del proyecto (opcional)
9. Flujo de trabajo diario
10. Problemas comunes
11. Checklist final

---

## 1. Acceso a GitHub

El repositorio está en la cuenta de Tarín y es **público**: cualquiera puede leerlo, pero solo los cinco integrantes pueden escribir en él.

| Integrante      | Usuario de GitHub                  |
| --------------- | ---------------------------------- |
| Alejandro Tarín | `T4R1N256` (dueño del repositorio) |
| Diego Galindo   | `Diego-Galindo98`                  |
| Jesús Hernández | `EduardGarrido`                    |
| Jared Beltrán   | `JBeltran16`                       |
| Yahir Enríquez  | `CodigaBorealis`                   |

1. **Acepta la invitación.** Tarín te invita como colaborador. Te llega por correo y también aparece en tus notificaciones de GitHub. Sin aceptarla no podrás subir cambios.
2. **Configura una llave SSH.** GitHub no acepta tu contraseña para `git push`. La forma más sencilla es una llave SSH:

   ```bash
   ssh-keygen -t ed25519 -C "tu-correo-de-github@ejemplo.com"   # Enter en todo para aceptar los valores por defecto
   cat ~/.ssh/id_ed25519.pub                                    # copia todo lo que imprime
   ```

   En GitHub: foto de perfil → **Settings → SSH and GPG keys → New SSH key**. Pega la llave y guarda. Luego comprueba la conexión:

   ```bash
   ssh -T git@github.com
   # Debe responder: "Hi <tu-usuario>! You've successfully authenticated..."
   ```

## 2. Herramientas

Necesitas **Python 3.12**, **Git** y **PostgreSQL 16 o superior**. Elige tu sistema operativo.

### Linux (Ubuntu 24.04 o similar)

```bash
sudo apt update
sudo apt install python3 python3-venv git postgresql
python3 --version        # debe decir 3.12.x
```

`python3-venv` es necesario: sin él, el entorno virtual no se crea. Si tu distribución trae otra versión de Python, instala la 3.12 antes de seguir.

### Windows

1. **Python 3.12** desde python.org. En el instalador, marca **"Add python.exe to PATH"**.
2. **Git** desde git-scm.com. Incluye **Git Bash**: usa Git Bash para todos los comandos de esta guía, así funcionan igual que en Linux.
3. **PostgreSQL 16** con el instalador de postgresql.org. **Anota la contraseña** que le asignes al usuario `postgres`; la necesitarás en la sección 6.

### macOS

```bash
brew install python@3.12 git postgresql@16
brew services start postgresql@16
```

### En todos los sistemas: tu identidad en Git

```bash
git config --global user.name "Tu Nombre"
git config --global user.email "tu-correo-de-github@ejemplo.com"
```

Usa el mismo correo de tu cuenta de GitHub; así tus commits aparecen a tu nombre.

## 3. Clonar el repositorio

```bash
git clone git@github.com:T4R1N256/SGFT.git
cd SGFT
```

La carpeta que se crea es la **raíz del proyecto**: ahí están `manage.py`, `CLAUDE.md` y `requirements.txt`. Todos los comandos siguientes se corren desde ahí.

## 4. Entorno virtual y dependencias

El entorno virtual (`venv`) aísla las librerías del proyecto de las de tu sistema.

```bash
python3 -m venv venv              # Windows: python -m venv venv   ·   macOS: python3.12 -m venv venv
source venv/bin/activate          # Windows (Git Bash): source venv/Scripts/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
```

Cuando el entorno está activo, la terminal muestra **`(venv)`** al inicio de la línea. **Actívalo cada vez que abras una terminal nueva**; si no aparece `(venv)`, `pip` instalaría las librerías fuera del proyecto.

Las versiones están fijadas en `requirements.txt` (Django 5.2 LTS y compañía), así que todos tenemos exactamente las mismas. No instales otras versiones por tu cuenta.

## 5. Archivo `.env`

La configuración sensible no está en el código, porque el repositorio es público: vive en un archivo `.env` que **cada quien crea en su computadora y nunca se sube**.

```bash
cp .env.example .env
python -c "import secrets; print(secrets.token_urlsafe(50))"   # genera tu clave secreta
```

Abre `.env` con tu editor y déjalo así, pegando la clave que generaste:

```
DJANGO_SECRET_KEY=pega-aqui-la-clave-generada
DJANGO_DEBUG=True
DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1
DJANGO_CSRF_TRUSTED_ORIGINS=
DJANGO_SECURE_SSL_REDIRECT=False
DATABASE_URL=postgres://sgft:sgft@localhost:5432/sgft
```

**Reglas:**

- Sin comillas ni espacios alrededor del `=`.
- Cada integrante tiene **su propia** clave; no tienen que coincidir.
- `git status` nunca debe mostrar `.env`. Si lo muestra, avisa antes de hacer commit.

## 6. Base de datos PostgreSQL

Vas a crear un usuario `sgft` y una base `sgft` en tu PostgreSQL local. Primero entra a la consola de administración; **la forma cambia según el sistema**:

| Sistema     | Cómo entrar                                                                                                                      |
| ----------- | -------------------------------------------------------------------------------------------------------------------------------- |
| **Linux**   | `sudo -u postgres psql` — **no** uses `psql -U postgres`: Linux usa autenticación _peer_ y responde `Peer authentication failed` |
| **Windows** | Menú Inicio → **SQL Shell (psql)** → Enter en todo y, al final, la contraseña de `postgres` que anotaste                         |
| **macOS**   | `psql postgres` (Homebrew usa tu usuario de macOS como administrador)                                                            |

Dentro de la consola, crea el usuario y la base:

```sql
CREATE USER sgft WITH PASSWORD 'sgft' CREATEDB;
CREATE DATABASE sgft OWNER sgft;
\q
```

`CREATEDB` es necesario para que `python manage.py test` pueda crear su propia base de pruebas.

**Comprueba la conexión como la hará Django** (por red, con usuario y contraseña):

```bash
psql "postgres://sgft:sgft@localhost:5432/sgft" -c "SELECT 'conexion OK';"
```

Si responde `conexion OK`, la base está lista. La contraseña `sgft` solo es aceptable porque la base vive en tu computadora; la de producción es otra y nunca va en el repositorio.

## 7. Inicializar y comprobar el proyecto

```bash
python manage.py check              # debe decir: System check identified no issues
python manage.py migrate            # crea las tablas
python manage.py createsuperuser    # tu usuario para entrar al admin
python manage.py test               # debe terminar con: OK
python manage.py runserver
```

Abre `http://127.0.0.1:8000/admin/` y entra con el superusuario que creaste. En tu ficha de usuario, el campo **Rol** debe decir **Administrador**. La raíz `/` responde 404, y eso es normal: todavía no hay página de inicio.

Para detener el servidor: `Ctrl + C`.

## 8. Claude y la skill del proyecto (opcional, recomendado)

El repositorio trae la skill `sgft-organizacion-entregables` en `.claude/skills/`. Te dice dónde va cada archivo y quién lo revisa.

- **Claude Code** la carga sola al trabajar dentro del repositorio.
- **Claude en el navegador o la app:** súbela en **Customize → Skills**. Para eso tiene que estar activada la ejecución de código en _Settings → Capabilities_.

También puedes consultar el mapa sin Claude:

```bash
python .claude/skills/sgft-organizacion-entregables/scripts/dueno_de_ruta.py --persona <tu-nombre>   # qué te toca
python .claude/skills/sgft-organizacion-entregables/scripts/dueno_de_ruta.py apps/pos/views.py       # de quién es un archivo
```

Usa como `<tu-nombre>` uno de estos: `diego`, `jesus`, `jared`, `tarin` o `yahir`.

## 9. Flujo de trabajo diario

**Al empezar el día (o antes de crear una rama):**

```bash
git switch main
git pull
pip install -r requirements.txt     # por si alguien agregó una dependencia
python manage.py migrate            # por si Jesús subió una migración
```

**Para trabajar en una tarea:**

```bash
git switch -c feat/RF-nn-descripcion-corta     # sin RF (infraestructura): feat/WBS-x.y.z-descripcion
# ... programas ...
python manage.py test
git add .
git status                                     # revisa que no aparezcan .env, venv/ ni db.sqlite3
python .claude/skills/sgft-organizacion-entregables/scripts/dueno_de_ruta.py --revisar $(git diff --cached --name-only)
git commit -m "feat(RF-nn): qué hace el cambio"
git push -u origin feat/RF-nn-descripcion-corta
```

Luego abre el Pull Request en GitHub y llena la plantilla. **Tarín aprueba y fusiona todos los PR.** Si el PR es de Tarín, lo aprueba otra persona de la ruta. El dueño de cada archivo tocado recibe la solicitud de revisión automáticamente.

**Reglas que no se rompen:**

- Nunca `git push` directo a `main` (GitHub lo bloquea de todos modos).
- **Solo Jesús corre `makemigrations`** y sube migraciones. Si necesitas un campo nuevo, pídeselo por issue.
- Nunca subas `.env`, credenciales ni datos reales del negocio.
- Los nombres de archivos y carpetas de código van en inglés; la app del punto de venta es `pos`.
- Antes de crear un archivo nuevo, consulta el mapa. Si su ruta no está, pregúntale a Tarín dónde va.

## 10. Problemas comunes

| Síntoma                                                             | Causa                                                                | Solución                                                                                                                                                                  |
| ------------------------------------------------------------------- | -------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `Peer authentication failed for user "postgres"`                    | En Linux, `psql -U postgres` usa autenticación _peer_                | Entra con `sudo -u postgres psql`                                                                                                                                         |
| `password authentication failed for user "sgft"`                    | La contraseña de `DATABASE_URL` no coincide con la del `CREATE USER` | Revisa `.env`, o cambia la contraseña en psql: `ALTER USER sgft WITH PASSWORD 'sgft';`                                                                                    |
| `connection refused` / `could not connect to server`                | PostgreSQL está apagado                                              | Linux: `sudo systemctl start postgresql` (y `enable` para que arranque solo) · macOS: `brew services start postgresql@16` · Windows: servicio "postgresql" en _Servicios_ |
| `Missing environment variable DJANGO_SECRET_KEY` (o `DATABASE_URL`) | No existe `.env`, no está en la raíz o la variable está mal escrita  | Repite la sección 5 desde la raíz del proyecto                                                                                                                            |
| `permission denied to create database` al correr las pruebas        | El usuario `sgft` no tiene `CREATEDB`                                | En psql: `ALTER USER sgft CREATEDB;`                                                                                                                                      |
| `ensurepip is not available` al crear el venv                       | Falta el paquete de entornos virtuales                               | Linux: `sudo apt install python3-venv`                                                                                                                                    |
| `ModuleNotFoundError: No module named 'django'`                     | El entorno virtual no está activo                                    | Actívalo (sección 4) y verifica que aparezca `(venv)`                                                                                                                     |
| `Cannot import 'pos'`                                               | Un `apps.py` dice `name = 'pos'` en lugar de `'apps.pos'`            | Avisa en el equipo: el esqueleto ya viene correcto, así que algo se modificó                                                                                              |
| `Error: That port is already in use`                                | Ya hay un servidor corriendo                                         | Ciérralo, o usa otro puerto: `python manage.py runserver 8001`                                                                                                            |
| `Permission denied (publickey)` al clonar o hacer push              | La llave SSH no está registrada en GitHub                            | Repite la sección 1, paso 2                                                                                                                                               |

Si algo no aparece aquí, avisa en el canal del equipo con el mensaje de error completo. Si lo resuelves, agrega la fila a esta tabla en tu siguiente PR.

## 11. Checklist final

- [ ] Acepté la invitación y `ssh -T git@github.com` me saluda por mi usuario.
- [ ] `python3 --version` (o `python --version`) dice 3.12.
- [ ] Clonado el repositorio y la terminal muestra `(venv)` dentro de la carpeta del proyecto.
- [ ] `pip install -r requirements.txt` terminó sin errores.
- [ ] Tengo `.env` con mi propia `DJANGO_SECRET_KEY`, y `git status` no lo muestra.
- [ ] `psql "postgres://sgft:sgft@localhost:5432/sgft" -c "SELECT 1;"` responde.
- [ ] `python manage.py test` termina en `OK`.
- [ ] Entré a `http://127.0.0.1:8000/admin/` y mi usuario tiene rol Administrador.
- [ ] Sé qué me toca: `dueno_de_ruta.py --persona <mi-nombre>`.
