# Parrot Inbox Service - Repository Overview

Welcome to the **Parrot Inbox Service**! This is a core Node.js TypeScript application that manages multi-channel communications, analytics, and background tasks.

## 🚀 Technology Stack

- **Framework**: [Express.js](https://expressjs.com/) (Backend API)
- **Language**: [TypeScript](https://www.typescriptlang.org/)
- **Databases**:
    - **PostgreSQL** (via TypeORM) for structured data.
    - **MongoDB** for flexible messaging and document data.
    - **Redis** for caching and session management.
    - **Elasticsearch** for high-performance searching and indexing.
- **Messaging & Queues**:
    - **RabbitMQ** (via `amqplib`) for distributed messaging.
    - **BullMQ** for internal background jobs and task management.
- **Real-time**: [Socket.io](https://socket.io/) for bidirectional communication.
- **Logging**: [Winston](https://github.com/winstonjs/winston) with Logstash support.

---

## 📂 Directory Structure

The codebase is organized into modular directories within `src/`:

| Directory      | Purpose                                                                          |
| :------------- | :------------------------------------------------------------------------------- |
| `routes/`      | API route definitions and entry points for HTTP requests.                        |
| `services/`    | Core business logic and integrations (HealthCheck, Initialization, etc.).        |
| `dashboard/`   | Logic specific to analytics and reporting (where you'll find `sourceAnalytics`). |
| `models/`      | Data schemas (primarily MongoDB/Mongoose).                                       |
| `entities/`    | Database entities for TypeORM (PostgreSQL).                                      |
| `db/`          | Database client initializations (Mongo, Postgres, ES, Redis).                    |
| `consumer/`    | RabbitMQ and BullMQ consumers/workers for background processing.                 |
| `socket/`      | Socket.io event handlers and logic.                                              |
| `helpers/`     | Reusable utilities like Logging, Config, and Endpoints.                          |
| `middlewares/` | Express middlewares (Error handling, Authentication, Tracing).                   |

---

## 📞 Request Flow - "Where the call happens"

Understanding how a request travels through the system is key. Here is a typical flow for an **Analytics Request**:

### 1. Entry Point: `src/app.ts`

All HTTP requests enter here. The app initializes middlewares (like `setTrackingId`) and attaches various routers.

```typescript
app.use('/dashboard', dashboardRouter);
```

### 2. Router: `src/routes/dashboardRouter.ts`

The router catches the specific path (e.g., `POST /total/stats`) and extracts headers like `tenant-id`. It then hands over the work to a high-level service.

### 3. Service Layer: `src/dashboard/sourceAnalytics/AnalyticsService.ts`

This service acts as a coordinator. It doesn't perform the math itself; instead, it uses a **Factory** to find the right tool for the job.

```typescript
const analyticsService = AnalyticsHandlerFactory.getService(request.source);
return analyticsService.summarizeByHours(request);
```

### 4. Factory & Concrete Implementation

The `AnalyticsHandlerFactory` looks at the `source` (e.g., "voice", "telephony", "sms") and returns the corresponding service:

- `VoiceAnalyticsService.ts`
- `TelephonyAnalyticsService.ts`
- `SMSAnalyticsService.ts`

These concrete services perform the actual database queries (Postgres/Mongo) and aggregate the data for the frontend.

---

## 🛠 Startup & Initialization

When the application starts, it runs `InitializationService.init()`. This performs a series of critical tasks:

1.  **DB Connections**: Establishes connections to Postgres, Mongo, Redis, and Elasticsearch.
2.  **Configuration**: Loads dynamic properties and endpoints.
3.  **Consumers/Workers**: Starts RabbitMQ consumers and BullMQ workers to begin processing background tasks.
4.  **Sockets**: Attaches event handlers to the Socket.io server.
5.  **Health Check**: Verifies the system is "healthy" before it starts accepting traffic.

---

## 💻 Local Development

To run the project locally, use the following commands:

- **Install Dependencies**: `npm install`
- **Run Dev Mode**: `npm run start:local-dev`
    - This uses `ts-node-dev` for hot-reloading and sets the `NODE_ENV` to `dev_k8s`.
- **Build**: `npm run dev` (This clears the `bin/` folder, compiles via `tsc`, and runs the JS).

---

## 📝 Key Design Patterns

- **Factory Pattern**: Heavily used for analytics and message consumers to handle multi-source data uniformly.
- **Singleton Database Clients**: Ensures only one connection pool exists per database type.
- **Service-Oriented Architecture**: Keeps business logic separated from the transport layer (HTTP/Socket).
