# 本地调试与一键启动指南

本文用于面试现场修改 Python、Java、React 或 TypeScript 代码后的快速验证。目标是从仓库根目录执行一条命令，等待四个服务就绪并在浏览器中看到最新页面。

## 1. 当前结论

项目有四个运行组件：

| 服务 | 技术 | 本地端口 | 依赖 |
|---|---|---:|---|
| `ml-api` | Python 3.12、FastAPI | 8000 | 模型产物 |
| `estimator-api` | Python 3.12、FastAPI | 8001 | `ml-api` |
| `market-api` | Java 21、Spring Boot | 8080 | `ml-api`、原始 CSV |
| `web` | Node.js、Next.js | 3000 | Estimator、Market |

检查前，Docker Compose 已经能够一条命令编排所有服务，但非 Docker 模式没有跨组件启动入口。现在已经补充：

- `scripts/start-local.ps1`：非 Docker 一键启动，等待健康并自动打开浏览器。
- `scripts/stop-local.ps1`：停止上述脚本启动的进程。
- `scripts/status-local.ps1`：检查四个端点。
- `scripts/start-docker.ps1`：构建、启动完整 Compose，等待健康并打开浏览器。

2026-08-19 的当前电脑实测结果：非 Docker 启动器成功启动四个服务，四个状态端点均返回 HTTP 200，Portal 在真实浏览器中正常渲染且没有控制台错误。Docker Compose 配置通过 `docker compose config --quiet`；当前 Docker Desktop 的 WSL 引擎发生 `DockerDesktop/Wsl/ExecError`，所以本轮没有完成容器运行时复验。这是本机 Docker/WSL 状态，不是 Compose 配置错误；面试现场可直接使用已经实测通过的非 Docker 一键入口兜底。

## 2. 面试现场最短路径

打开 PowerShell，进入仓库根目录：

```powershell
cd D:\1_myCode\3-interview\housing-price-fullstack-interview
```

不使用 Docker，一条命令启动并打开浏览器：

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\start-local.ps1
```

使用 Docker，一条命令构建、启动并打开浏览器：

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\start-docker.ps1
```

Portal 地址：<http://localhost:3000>。

如果只是希望启动服务而不自动打开浏览器：

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\start-local.ps1 -NoBrowser
```

## 3. 不使用 Docker

### 3.1 一次性前置条件

本地直接运行需要：

- Python 3.12.13，以及两个服务各自的 `.venv`。
- Node.js 24.18.0。
- Corepack 提供的 pnpm 11.15.1。
- JDK 21。
- 可用端口 3000、8000、8001、8080。

创建 Python 环境：

```powershell
cd D:\1_myCode\3-interview\housing-price-fullstack-interview\services\ml-api
uv sync --frozen

cd ..\estimator-api
uv sync --frozen
```

项目将 `uv` 锁定为 0.11.32。如果全局版本不匹配，需要先安装或切换至该版本。当前电脑已经存在两个可用虚拟环境，一键启动脚本会直接复用它们。

准备前端：

```powershell
nvm use 24.18.0

cd D:\1_myCode\3-interview\housing-price-fullstack-interview\apps\web
corepack pnpm install --frozen-lockfile
```

`start-local.ps1` 会读取 `apps/web/package.json`，优先从 `NVM_HOME` 自动定位 Node.js 24.18.0，不依赖当前终端恰好激活了哪个 Node 版本。如果 `node_modules` 不存在，它会通过 Corepack 自动执行一次冻结安装。

Java 使用 Maven Wrapper，不要求单独安装 Maven，但必须有 JDK 21。启动器会尝试读取 `JAVA_HOME`，也会检查 Windows 常见的 JDK 21 安装目录。

### 3.2 分别启动四个服务

需要四个 PowerShell 终端，并按依赖顺序启动。

#### 第一个终端：ML API

```powershell
cd D:\1_myCode\3-interview\housing-price-fullstack-interview\services\ml-api

.\.venv\Scripts\python.exe -m uvicorn app.main:app `
  --reload `
  --host 127.0.0.1 `
  --port 8000
```

验证：

```powershell
Invoke-RestMethod http://localhost:8000/ready
```

Swagger：<http://localhost:8000/docs>。

#### 第二个终端：Estimator API

```powershell
cd D:\1_myCode\3-interview\housing-price-fullstack-interview\services\estimator-api

$env:ML_API_BASE_URL = "http://127.0.0.1:8000"
$env:ML_API_TIMEOUT_SECONDS = "5"

.\.venv\Scripts\python.exe -m uvicorn app.main:app `
  --reload `
  --host 127.0.0.1 `
  --port 8001
```

验证：

```powershell
Invoke-RestMethod http://localhost:8001/ready
```

Swagger：<http://localhost:8001/docs>。

#### 第三个终端：Market API

```powershell
cd D:\1_myCode\3-interview\housing-price-fullstack-interview\services\market-api

$env:JAVA_HOME = "C:\Program Files\Java\latest\jdk-21"
$env:Path = "$env:JAVA_HOME\bin;$env:Path"
$env:ML_API_BASE_URL = "http://127.0.0.1:8000"
$env:ML_API_TIMEOUT_SECONDS = "5"

.\mvnw.cmd spring-boot:run
```

如果本机 JDK 位于其他目录，应修改 `JAVA_HOME`。验证：

```powershell
Invoke-RestMethod http://localhost:8080/health
Invoke-RestMethod http://localhost:8080/api/v1/market/summary
```

#### 第四个终端：Web

```powershell
nvm use 24.18.0

cd D:\1_myCode\3-interview\housing-price-fullstack-interview\apps\web

$env:ESTIMATOR_API_BASE_URL = "http://127.0.0.1:8001"
$env:MARKET_API_BASE_URL = "http://127.0.0.1:8080"
$env:NEXT_PUBLIC_BASE_PATH = ""

corepack pnpm dev
```

打开 <http://localhost:3000>。

### 3.3 一条命令启动全部服务

从仓库根目录执行：

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\start-local.ps1
```

脚本会依次完成：

1. 检查两个 Python 虚拟环境、Maven Wrapper 和前端清单。
2. 自动定位 JDK 21、Node.js 24.18.0 和 Corepack。
3. 在模型产物缺失时运行一次训练。
4. 在 `node_modules` 缺失时执行冻结依赖安装。
5. 检查 3000、8000、8001、8080 端口。
6. 停止上一次由该脚本记录的本地开发进程。
7. 启动 ML，并等待 `/ready`。
8. 启动 Estimator，并等待 `/ready`。
9. 启动 Market，并等待 `/health`。
10. 启动 Web，并等待 `/api/ready`。
11. 恢复 Next.js 启动时可能改写的 `next-env.d.ts`，避免产生无关 Git 变化。
12. 自动打开 <http://localhost:3000>。

Python 服务使用 Uvicorn `--reload`，Next.js 使用开发模式，因此保存 Python、React、TypeScript 或 CSS 文件后通常会自动刷新。Spring Boot 当前没有引入 DevTools；修改 Java 后，重新执行同一条启动命令即可保证四个服务都使用最新代码。

### 3.4 查看状态、日志和停止

状态检查：

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\status-local.ps1
```

停止：

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\stop-local.ps1
```

启动器不会把运行日志写入 Git 跟踪目录。每次运行的日志保存在：

```text
tmp/local-dev/<启动时间>/
```

每个服务分别有 `.out.log` 和 `.err.log`。`tmp/`、`*.log` 已被 `.gitignore` 忽略。

## 4. 使用 Docker

### 4.1 前置条件

- Docker Desktop 或兼容的 Docker Engine。
- Docker Compose v2。
- Docker Engine 已经启动。
- 端口 3000、8000、8001、8080 没有被本地开发进程占用。

检查：

```powershell
docker --version
docker compose version
docker info
docker compose config --quiet
```

如果刚刚运行过非 Docker 模式，先执行：

```powershell
.\scripts\stop-local.ps1
```

如果 `docker info` 报告 `DockerDesktop/Wsl/ExecError`，应先修复或重启 Docker Desktop/WSL，再执行 Compose。不要为了启动本项目删除 Docker 数据发行版、镜像或数据卷。

### 4.2 一条命令启动所有服务并打开浏览器

推荐使用仓库脚本：

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\start-docker.ps1
```

它会执行 Compose 配置验证、构建镜像、后台启动、健康等待，并在成功后打开 <http://localhost:3000>。

如果镜像已经是最新的，希望跳过构建：

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\start-docker.ps1 -NoBuild
```

直接使用 Docker Compose 的等价启动命令：

```powershell
docker compose up --build -d --wait --wait-timeout 300
```

注意：根 Compose 没有把源代码挂载进容器。修改代码后，`docker compose restart` 不会包含新代码，必须重新执行带 `--build` 的命令。

### 4.3 常见 Docker Compose 命令

验证最终配置：

```powershell
docker compose config
docker compose config --quiet
```

查看服务和健康状态：

```powershell
docker compose ps
docker compose top
```

查看全部日志：

```powershell
docker compose logs --tail 200
docker compose logs -f --tail 100
```

只查看某个服务：

```powershell
docker compose logs -f --tail 100 ml-api
docker compose logs -f --tail 100 estimator-api
docker compose logs -f --tail 100 market-api
docker compose logs -f --tail 100 web
```

修改 Python 后，只重建相关服务：

```powershell
docker compose up --build -d --wait ml-api estimator-api
```

修改 Java 后：

```powershell
docker compose up --build -d --wait market-api
```

修改前端后：

```powershell
docker compose up --build -d --wait web
```

强制无缓存重建单个镜像：

```powershell
docker compose build --no-cache web
docker compose up -d --wait web
```

重启现有容器但不重建镜像：

```powershell
docker compose restart
docker compose restart market-api
```

临时停止和重新启动现有容器：

```powershell
docker compose stop
docker compose start
```

关闭并移除本项目容器和网络：

```powershell
docker compose down
```

查看 Docker 磁盘使用：

```powershell
docker system df
```

清理构建缓存前先确认不再需要旧缓存：

```powershell
docker builder prune
```

不要在面试前随意运行 `docker system prune -a --volumes`。它可能删除其他项目仍需要的镜像、缓存和数据卷。

## 5. 修改后的推荐验证流程

### 5.1 修改 Python 后端

先运行目标服务的快速质量检查：

```powershell
cd services\ml-api
.\.venv\Scripts\ruff.exe check app tests
.\.venv\Scripts\mypy.exe app
.\.venv\Scripts\pytest.exe -q
```

Estimator 使用相同命令，只需把目录换成 `services\estimator-api`。然后回到仓库根目录运行 `start-local.ps1`，通过 Swagger 或 Portal 检查。

### 5.2 修改 Java 后端

```powershell
cd services\market-api
$env:JAVA_HOME = "C:\Program Files\Java\latest\jdk-21"
.\mvnw.cmd test
```

测试通过后重新执行一键启动命令，并在 Market 页面检查数据、筛选或导出行为。

### 5.3 修改前端

```powershell
cd apps\web
corepack pnpm test
corepack pnpm typecheck
corepack pnpm lint
```

若本地开发栈已经运行，Next.js 会热更新；否则执行 `start-local.ps1`。

## 6. 常见故障排查

### 6.1 端口被占用

```powershell
Get-NetTCPConnection -State Listen |
  Where-Object LocalPort -In 3000,8000,8001,8080 |
  Select-Object LocalAddress,LocalPort,OwningProcess
```

不要让非 Docker 栈和 Docker 栈同时占用相同端口。使用对应的 `stop-local.ps1` 或 `docker compose down` 关闭其中一套。

### 6.2 启动脚本报告版本缺失

- Python：检查两个 `.venv\Scripts\python.exe`。
- Node：运行 `nvm list`，确认 24.18.0 已安装。
- pnpm：运行 `corepack pnpm --version`，应为 11.15.1。
- Java：运行 `$env:JAVA_HOME` 和 `& "$env:JAVA_HOME\bin\java.exe" -version`。

### 6.3 后端正常但页面失败

按依赖顺序检查：

```powershell
Invoke-RestMethod http://localhost:8000/ready
Invoke-RestMethod http://localhost:8001/ready
Invoke-RestMethod http://localhost:8080/health
Invoke-RestMethod http://localhost:3000/api/ready
```

先解决 ML，再检查 Estimator 和 Market，最后检查 Web。不要仅以“进程还在”判断成功。

## 7. 面试中的英文说明

> For rapid feedback, I run the services locally with hot reload and targeted tests. The repository provides one PowerShell command that starts the services in dependency order, waits for readiness, and opens the browser. Before final delivery, I rebuild the Docker Compose stack to verify container networking and runtime configuration.
