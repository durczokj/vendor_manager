```mermaid
erDiagram
    %% Define entities and relationships
    COMPANY {
        int id PK
        string name
        string email
    }

    CONTRACT {
        int id PK
        string name
        string status
        int size
    }

    COST_CENTER {
        int id PK
        string name
    }

    ENGAGEMENT {
        int id PK
        string person_id FK
        date start_date
        date end_date
        decimal daily_rate
        decimal fte
    }

    ENGAGEMENT_ORDER_VERSION_ASSIGNMENT {
        int id PK
        int engagement_id FK
        int order_version_id FK
    }

    ENGAGEMENT_UNDERTAKING_ASSIGNMENT {
        int id PK
        int engagement_id FK
        int undertaking_id FK
        date start_date
        date end_date
        decimal percentage
    }

    LEAVE {
        int id PK
        string person_id FK
        date start_date
        date end_date
        decimal percentage
    }

    ORDER {
        int id PK
        int company_id FK
        string name
    }

    ORDER_VERSIONS {
        int id PK
        int order_id FK
        int contract_id FK
        int version_number
        date start_date
        date end_date
    }

    PERSON {
        string id PK
        string first_name
        string last_name
        string description
        string location
        int user_id FK
    }

    UNDERTAKING {
        int id PK
        string name
        int cost_center_id FK
        string manager_id FK
    }

    USER {
        int id PK
        string username
        string email
        string password
    }

    GROUP {
        int id PK
        string name
    }

    USER_GROUP {
        int id PK
        int user_id FK
        int group_id FK
    }

    PERMISSION {
        int id PK
        string codename
        string name
    }

    GROUP_PERMISSION {
        int id PK
        int group_id PK
        int permission_id PK
    }


    %% Define relationships
    COMPANY ||--o{ ORDER : "has"

    ORDER ||--o{ ORDER_VERSIONS : "has"
    ORDER_VERSIONS ||--o{ ENGAGEMENT_ORDER_VERSION_ASSIGNMENT : "has"
    ENGAGEMENT ||--o{ ENGAGEMENT_ORDER_VERSION_ASSIGNMENT : "has"

    PERSON ||--o{ ENGAGEMENT : "has"

    PERSON ||--o| USER : "has"

    USER ||--o{ USER_GROUP : "has"
    GROUP ||--o{ USER_GROUP : "has"

    GROUP ||--o{ GROUP_PERMISSION : "has"
    PERMISSION ||--o{ GROUP_PERMISSION : "has"

    PERSON ||--o{ LEAVE : "has"

    CONTRACT ||--o| ORDER_VERSIONS : "backs"

    COST_CENTER ||--o{ UNDERTAKING : "has"
    PERSON ||--o{ UNDERTAKING : "manages"

    ENGAGEMENT ||--o{ ENGAGEMENT_UNDERTAKING_ASSIGNMENT : "has"
    UNDERTAKING ||--o{ ENGAGEMENT_UNDERTAKING_ASSIGNMENT : "has"
```

## Notes on the diagram

- **`PERSON.id`** is a business‑assigned string (max 6), not an integer. FK columns that reference it (`ENGAGEMENT.person_id`, `LEAVE.person_id`, `UNDERTAKING.manager_id`) are therefore string‑typed.
- **`PERSON.user_id`** is optional (nullable `OneToOneField`). A `Person` may exist without a login account; every logged‑in `User` must be linked to exactly one `Person` (see `FR‑23`).
- **`CONTRACT ↔ ORDER_VERSIONS`** is 1:1 by design. Each contract backs at most one order version; creating a new order version requires a new contract.
- **`COST_CENTER`** is a first‑class entity with its own business‑assigned integer PK (`FR‑7`).
- **Django auth tables** (`USER`, `GROUP`, `USER_GROUP`, `PERMISSION`, `GROUP_PERMISSION`) are shown for completeness. Which of them is used to model the three roles (`Person`, `UndertakingManager`, `Admin`) is an implementation choice per `FR‑25`.
- **`ENGAGEMENT.daily_rate`** and **`ENGAGEMENT.fte`** are `decimal`. `fte ∈ [0, 1]` per `FR‑12`.
- **`LEAVE.percentage`** and **`ENGAGEMENT_UNDERTAKING_ASSIGNMENT.percentage`** are `decimal(3, 2)` in `[0, 1]` per `FR‑17` / `OQ‑1`.
