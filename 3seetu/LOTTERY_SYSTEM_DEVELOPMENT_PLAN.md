# Lottery Game System — Development Plan

## 1. Objective

Build a configurable number-guessing game with three game types.

The system should support:

1. 3-digit game
2. 5-digit game
3. 5-digit + 1 Power Digit game

The system uses virtual/game credits rather than real money.

The architecture should be designed so that additional lottery/game formats can be introduced without rewriting the core game engine.

---

# 2. Game Types

## Type 1 — 3 Digit

### Player Entry

Player selects exactly 3 single digits.

Example:

    4 - 7 - 2

Entry cost:

    120 game credits

### Winning Number

The system generates three digits.

Example:

    4 - 7 - 2

### Prize Rules

| Match | Reward |
|---|---:|
| First 3 digits match | 25,000 |
| First 2 digits match | 1,000 |
| First 1 digit matches | 120 refund |
| No digits match | 0 |

Important:

Matching is positional.

For example:

Winning:

    4 7 2

Player:

    4 7 9

Result:

    First 2 match → 1,000

Player:

    7 4 2

Result:

    No first-position match → 0

The system should NOT treat this as an unordered combination.

---

# 3. Type 2 — 5 Digit

The second game uses five single digits.

Example:

    4 - 7 - 2 - 8 - 1

The exact entry price and prize structure should be configurable.

Recommended configuration model:

```json
{
  "game_type": "FIVE_DIGIT",
  "digits": 5,
  "entry_price": 0,
  "prizes": {
    "5_match": 0,
    "4_match": 0,
    "3_match": 0,
    "2_match": 0,
    "1_match": 0
  }
}
```

This allows the business team to change pricing/prizes without changing application code.

Matching should be positional unless the business rules explicitly specify otherwise.

---

# 4. Type 3 — 5 Digit + Power Digit

Player selects:

    Digit 1
    Digit 2
    Digit 3
    Digit 4
    Digit 5
    Power Digit

Example:

    4 - 7 - 2 - 8 - 1
    Power: 6

Winning result:

    4 - 7 - 2 - 8 - 1
    Power: 6

The Power Digit should be evaluated separately from the five primary digits.

Example configuration:

```json
{
  "game_type": "FIVE_DIGIT_POWER",
  "digits": 5,
  "power_digits": 1,
  "entry_price": 0,
  "prizes": {
    "5_plus_power": 0,
    "5_without_power": 0,
    "4_plus_power": 0,
    "4_without_power": 0,
    "3_plus_power": 0
  }
}
```

The exact prize table should be finalized before implementation.

---

# 5. Core Architecture

Do NOT build three separate lottery implementations.

Build one generic game engine.

Architecture:

```text
                    ┌────────────────────┐
                    │     Client App     │
                    └─────────┬──────────┘
                              │
                              ▼
                    ┌────────────────────┐
                    │    API Gateway     │
                    └─────────┬──────────┘
                              │
                              ▼
                    ┌────────────────────┐
                    │   Game Service     │
                    └─────────┬──────────┘
                              │
             ┌────────────────┼────────────────┐
             ▼                ▼                ▼
       Game Config       Ticket Service    Result Engine
             │                │                │
             └────────────────┼────────────────┘
                              │
                              ▼
                    ┌────────────────────┐
                    │     Database       │
                    └────────────────────┘
```

---

# 6. Major Components

## 6.1 Game Service

Responsible for:

- Listing available games
- Returning game configuration
- Validating player selections
- Creating game entries
- Managing game lifecycle

Example:

```text
GET /games

GET /games/{gameId}

POST /games/{gameId}/tickets
```

---

# 7. Game Configuration

Game rules should live in configuration rather than application logic.

Example:

```json
{
  "game_type": "THREE_DIGIT",
  "digits": 3,
  "power_digits": 0,
  "entry_price": 120,
  "prizes": [
    {
      "match_level": 3,
      "reward": 25000
    },
    {
      "match_level": 2,
      "reward": 1000
    },
    {
      "match_level": 1,
      "reward": 120
    }
  ]
}
```

This means the engine can process different games using the same code.

---

# 8. Ticket Model

Every player entry should create a ticket.

Example:

```json
{
  "ticket_id": "TKT-100001",
  "user_id": "USER-1001",
  "game_id": "GAME-001",
  "game_type": "THREE_DIGIT",
  "numbers": [4, 7, 2],
  "power_number": null,
  "entry_price": 120,
  "status": "PENDING",
  "created_at": "2026-09-13T10:00:00Z"
}
```

For the Power Digit game:

```json
{
  "numbers": [4, 7, 2, 8, 1],
  "power_number": 6
}
```

---

# 9. Draw Model

A draw represents one completed lottery/game round.

Example:

```json
{
  "draw_id": "DRAW-10001",
  "game_id": "GAME-001",
  "winning_numbers": [4, 7, 2],
  "winning_power_number": null,
  "status": "COMPLETED",
  "draw_time": "2026-09-13T12:00:00Z"
}
```

For the Power Digit game:

```json
{
  "winning_numbers": [4, 7, 2, 8, 1],
  "winning_power_number": 6
}
```

---

# 10. Draw Lifecycle

Each draw should have a strict lifecycle.

```text
SCHEDULED
    │
    ▼
OPEN
    │
    ▼
CLOSED
    │
    ▼
DRAWING
    │
    ▼
RESULT_GENERATED
    │
    ▼
SETTLED
```

### SCHEDULED

Draw exists but entries are not yet accepted.

### OPEN

Players can purchase tickets.

### CLOSED

No additional tickets are accepted.

### DRAWING

Winning numbers are generated.

### RESULT_GENERATED

Winning numbers are persisted.

### SETTLED

All eligible tickets have been evaluated and rewards have been credited.

---

# 11. Critical Rule

Once a draw reaches `CLOSED`, the winning result must be generated independently of player tickets.

Do NOT:

```text
Read all player tickets
        ↓
Select a number that produces desired winners
```

Instead:

```text
Draw closes
     ↓
Generate random winning result
     ↓
Persist immutable result
     ↓
Evaluate tickets
```

This keeps the game logic deterministic and auditable.

---

# 12. Random Number Generation

Use a cryptographically secure random number generator.

For a single digit:

```text
0–9
```

For three digits:

```text
000–999
```

For five digits:

```text
00000–99999
```

Leading zeros must be allowed.

Examples:

```text
007
042
00019
90102
```

Do NOT store numbers purely as integers because:

```text
007
```

would become:

```text
7
```

Store the sequence either as:

```text
"007"
```

or:

```text
[0, 0, 7]
```

---

# 13. Match Engine

Create a generic matching engine.

For Type 1:

```text
Player:
4 7 2

Winner:
4 7 9

Position 1 → match
Position 2 → match
Position 3 → mismatch

Match level = 2
Reward = 1,000
```

Pseudo-code:

```text
match_count = 0

for i in positions:
    if player[i] == winning[i]:
        match_count += 1
    else:
        break
```

The `break` is important for the Type 1 rule because the prize is based on the consecutive prefix.

For example:

```text
Winner: 4 7 2
Player: 4 9 2
```

Only the first digit matches.

Result:

```text
1-match reward
```

Not:

```text
2 matches
```

because the third digit matching does not matter after the second position fails.

---

# 14. Power Digit Matching

For Type 3:

```text
Player:

4 7 2 8 1
Power: 6

Winner:

4 7 2 9 5
Power: 6
```

Primary digits:

```text
3 consecutive matches
```

Power digit:

```text
MATCH
```

The result engine should return:

```json
{
  "primary_match_count": 3,
  "power_match": true
}
```

Then the prize configuration determines the reward.

---

# 15. Prize Engine

Separate prize calculation from matching.

Flow:

```text
Ticket
   ↓
Match Engine
   ↓
Match Result
   ↓
Prize Engine
   ↓
Reward
```

Example:

```json
{
  "primary_match_count": 2,
  "power_match": false
}
```

Prize engine looks at game configuration and returns:

```text
1000
```

This separation makes future games easier to implement.

---

# 16. Wallet / Game Credits

Although this is not real money, use a wallet-like ledger rather than simply maintaining:

```text
balance = balance - 120
```

Use a transaction ledger.

Example:

```text
Wallet
  │
  ├── +1000  Promotional Credits
  ├── -120   Ticket Purchase
  ├── +25000 Winning Reward
  └── -50    Another Ticket
```

Transaction:

```json
{
  "transaction_id": "TXN-10001",
  "user_id": "USER-1001",
  "type": "TICKET_PURCHASE",
  "amount": -120,
  "reference_type": "TICKET",
  "reference_id": "TKT-100001"
}
```

This gives you an audit trail.

---

# 17. Idempotency

Very important.

Suppose result settlement runs twice.

Without protection:

```text
Winner receives:
25,000

Settlement runs again:

Winner receives:
25,000

Final:
50,000
```

This must never happen.

Use a unique settlement constraint:

```text
(ticket_id, draw_id)
```

A ticket can only be settled once for a particular draw.

---

# 18. Database Design

Recommended relational model:

```text
users
  │
  └── wallets
        │
        └── wallet_transactions


games
  │
  └── draws
        │
        └── tickets
              │
              └── ticket_results
```

Tables:

```text
users
games
game_configs
draws
tickets
ticket_results
wallets
wallet_transactions
audit_logs
```

---

# 19. Games Table

Example:

```sql
CREATE TABLE games (
    id UUID PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    game_type VARCHAR(50) NOT NULL,
    status VARCHAR(20) NOT NULL,
    created_at TIMESTAMP NOT NULL
);
```

---

# 20. Draws Table

```sql
CREATE TABLE draws (
    id UUID PRIMARY KEY,
    game_id UUID NOT NULL,
    winning_numbers VARCHAR(20),
    winning_power_number SMALLINT,
    status VARCHAR(30) NOT NULL,
    opened_at TIMESTAMP,
    closed_at TIMESTAMP,
    drawn_at TIMESTAMP,
    settled_at TIMESTAMP
);
```

---

# 21. Tickets Table

```sql
CREATE TABLE tickets (
    id UUID PRIMARY KEY,
    draw_id UUID NOT NULL,
    user_id UUID NOT NULL,
    numbers VARCHAR(20) NOT NULL,
    power_number SMALLINT,
    entry_price INTEGER NOT NULL,
    status VARCHAR(30) NOT NULL,
    created_at TIMESTAMP NOT NULL
);
```

---

# 22. Ticket Results

```sql
CREATE TABLE ticket_results (
    id UUID PRIMARY KEY,
    ticket_id UUID NOT NULL UNIQUE,
    draw_id UUID NOT NULL,
    primary_match_count INTEGER NOT NULL,
    power_match BOOLEAN NOT NULL DEFAULT FALSE,
    reward INTEGER NOT NULL DEFAULT 0,
    settled_at TIMESTAMP
);
```

---

# 23. API Design

## Get Games

```http
GET /api/v1/games
```

Response:

```json
[
  {
    "id": "GAME-001",
    "name": "3 Digit",
    "type": "THREE_DIGIT",
    "entry_price": 120
  },
  {
    "id": "GAME-002",
    "name": "5 Digit",
    "type": "FIVE_DIGIT",
    "entry_price": 0
  },
  {
    "id": "GAME-003",
    "name": "5 Digit Power",
    "type": "FIVE_DIGIT_POWER",
    "entry_price": 0
  }
]
```

---

# 24. Purchase Ticket

```http
POST /api/v1/draws/{drawId}/tickets
```

Request:

```json
{
  "numbers": [4, 7, 2]
}
```

Power game:

```json
{
  "numbers": [4, 7, 2, 8, 1],
  "power_number": 6
}
```

Validation:

```text
Correct number of digits
        ↓
Each digit is 0–9
        ↓
Power digit required if applicable
        ↓
Draw is OPEN
        ↓
User has sufficient game credits
        ↓
Create ticket
        ↓
Debit wallet
```

---

# 25. Result API

```http
GET /api/v1/draws/{drawId}/result
```

Example:

```json
{
  "draw_id": "DRAW-10001",
  "winning_numbers": [4, 7, 2],
  "status": "COMPLETED"
}
```

User's ticket result:

```http
GET /api/v1/tickets/{ticketId}/result
```

Response:

```json
{
  "ticket_id": "TKT-100001",
  "winning_numbers": [4, 7, 2],
  "selected_numbers": [4, 7, 9],
  "match_count": 2,
  "reward": 1000,
  "status": "WIN"
}
```

---

# 26. Admin System

Admin should be able to:

- Create game
- Configure entry price
- Configure prize tiers
- Schedule draws
- Open/close draws
- Trigger draw
- View winners
- View ticket statistics
- View credit transactions
- Reconcile settlements
- View audit logs

Admin should NOT be able to modify an already completed draw result.

---

# 27. Auditability

Every important event should be logged.

Example:

```text
DRAW_CREATED
DRAW_OPENED
TICKET_CREATED
WALLET_DEBITED
DRAW_CLOSED
WINNING_NUMBER_GENERATED
RESULT_PUBLISHED
TICKET_SETTLED
REWARD_CREDITED
```

Each event should contain:

```text
event_id
event_type
entity_id
user/admin
timestamp
metadata
```

---

# 28. Security

The client must NEVER generate the winning number.

Bad:

```text
Mobile App
   ↓
Generate winner
```

Correct:

```text
Backend
   ↓
Secure RNG
   ↓
Winning number
```

The client should only submit player selections.

The server determines:

- Entry validity
- Entry price
- Draw status
- Winning number
- Match
- Reward

Never trust these values from the client.

---

# 29. Concurrency

Potential situation:

```text
Draw closes at 12:00:00
```

Two requests arrive simultaneously:

```text
Request A → buy ticket
Request B → close draw
```

The database transaction must guarantee that a ticket cannot be created after the draw is closed.

Use:

- Database transaction
- Row locking where appropriate
- Draw status validation
- Idempotency keys

---

# 30. Settlement Architecture

For a small system:

```text
Draw completed
      ↓
Background worker
      ↓
Fetch tickets
      ↓
Evaluate
      ↓
Create result
      ↓
Credit reward
```

For a larger system:

```text
Draw Service
     ↓
DRAW_COMPLETED event
     ↓
Message Queue
     ↓
Settlement Workers
     ↓
Match Engine
     ↓
Wallet Service
```

Possible infrastructure:

```text
Kafka / Redpanda
Redis
PostgreSQL
```

But do not introduce Kafka immediately unless scale actually requires it.

---

# 31. Recommended Technology Stack

For a production-oriented first version:

```text
Backend:
Go / Node.js

Database:
PostgreSQL

Cache:
Redis

Frontend:
React / Next.js

Mobile:
Flutter

Background Jobs:
Worker service

Deployment:
Docker

Reverse Proxy:
Nginx

Observability:
Prometheus
Grafana
Structured logs
```

For a backend focused on lightweight services and concurrency, Go + PostgreSQL would be a strong choice.

---

# 32. Development Phases

## Phase 1 — Core Domain

Build:

```text
Game
GameConfig
Draw
Ticket
TicketResult
Prize
```

Implement:

```text
Game validation
Number validation
Match engine
Prize engine
```

---

## Phase 2 — Type 1

Implement the complete 3-digit game.

Rules:

```text
Entry = 120

3 prefix matches = 25,000
2 prefix matches = 1,000
1 prefix match = 120
0 = 0
```

Create extensive unit tests before implementing the other games.

---

# 33. Type 1 Test Cases

Winning:

```text
472
```

| Player | Result |
|---|---:|
| 472 | 25,000 |
| 471 | 1,000 |
| 479 | 1,000 |
| 492 | 120 |
| 172 | 0 |
| 742 | 0 |
| 000 | 0 |

Important:

```text
Winning: 472
Player: 472
```

→ 25,000

```text
Winning: 472
Player: 479
```

→ 1,000

```text
Winning: 472
Player: 499
```

→ 120

```text
Winning: 472
Player: 742
```

→ 0

---

# 34. Phase 3 — Type 2

Implement:

```text
5-digit selection
5-digit winning number
Configurable prize tiers
```

Reuse:

```text
Game Service
Draw Service
Ticket Service
Match Engine
Prize Engine
Wallet
Settlement
```

Only the game configuration should change.

---

# 35. Phase 4 — Type 3

Add:

```text
5 primary digits
+
1 Power Digit
```

Extend the existing match engine rather than creating a completely separate implementation.

---

# 36. Phase 5 — Wallet

Implement:

```text
Wallet
Wallet balance
Credit transaction
Debit transaction
Transaction history
Idempotency
```

Do not use floating-point numbers.

Use integer game credits:

```text
120
25000
1000
```

---

# 37. Phase 6 — Admin

Build admin dashboard for:

```text
Games
Draws
Tickets
Winners
Prize configuration
Credit transactions
Audit logs
```

---

# 38. Phase 7 — Frontend

Player flow:

```text
Login
  ↓
Choose Game
  ↓
Choose Draw
  ↓
Select Numbers
  ↓
Review
  ↓
Purchase Ticket
  ↓
Receive Ticket
  ↓
Wait for Draw
  ↓
View Result
  ↓
View Reward
```

---

# 39. Phase 8 — Testing

Test:

### Unit Tests

```text
Number validation
Match calculation
Prize calculation
Power digit matching
Wallet calculations
```

### Integration Tests

```text
Create ticket
Debit credits
Close draw
Generate result
Settle ticket
Credit reward
```

### Concurrency Tests

```text
Multiple ticket purchases
Ticket purchase during draw closing
Multiple settlement workers
Duplicate API requests
```

### Failure Tests

```text
Database failure
Worker failure
Duplicate settlement
Network retry
Application restart
```

---

# 40. Important Business Rules To Finalize

Before development of Types 2 and 3, define:

1. Entry price
2. Number of tickets allowed per user/draw
3. Whether duplicate selections are allowed
4. Whether leading zeroes are allowed
5. Draw frequency
6. Draw duration
7. Exact prize tiers
8. Whether Type 2 matching is positional
9. Whether Type 3 Power Digit is independent
10. Whether Power Digit can equal one of the five primary digits
11. Maximum reward
12. Whether unused/expired credits expire
13. Whether tickets can be cancelled
14. Whether a user can purchase after a draw closes
15. How ties / multiple winners are handled
16. Whether prizes are fixed or dynamically calculated
17. Whether there is a maximum number of tickets per draw

---

# 41. Suggested Repository Structure

```text
lottery-system/
│
├── cmd/
│   ├── api/
│   └── worker/
│
├── internal/
│   ├── game/
│   ├── draw/
│   ├── ticket/
│   ├── matching/
│   ├── prize/
│   ├── wallet/
│   ├── settlement/
│   ├── user/
│   └── audit/
│
├── migrations/
│
├── config/
│
├── tests/
│
├── docker/
│
└── README.md
```

---

# 42. Core Design Principle

The most important architectural decision is:

```text
Game Rules ≠ Game Engine
```

The engine should understand:

```text
"How do I validate numbers?"
"How do I compare numbers?"
"How do I calculate a reward?"
```

The configuration should determine:

```text
"How many digits?"
"How much does entry cost?"
"What counts as a win?"
"How much is the reward?"
"Is there a Power Digit?"
```

Therefore:

```text
                  ┌──────────────────┐
                  │   Generic Engine │
                  └────────┬─────────┘
                           │
             ┌─────────────┼──────────────┐
             ▼             ▼              ▼
        3 DIGIT         5 DIGIT       5 + POWER
        CONFIG          CONFIG          CONFIG
```

This makes the system extensible.

A future game such as:

```text
4 Digit
6 Digit
Pick 3
Pick 5
5 + Bonus
Daily Draw
Weekly Draw
```

can be added primarily through new configuration and only limited new logic where the matching rules genuinely differ.

---

# 43. First Development Milestone

The first working version should contain only:

```text
3-Digit Game
        ↓
120 Credit Entry
        ↓
Draw Creation
        ↓
Secure Random Number
        ↓
Ticket Creation
        ↓
Prefix Matching
        ↓
Prize Calculation
        ↓
Credit Reward
        ↓
Result Display
```

Once this is proven, Type 2 and Type 3 should be implemented on top of the same engine rather than duplicated.

---

# 44. Compliance / Product Boundary

The initial implementation should remain a virtual-credit game with no cash redemption or real-money wagering.

Before adding any mechanism where users purchase credits, win something of monetary value, withdraw rewards, or otherwise wager money, obtain an appropriate legal/compliance review for the jurisdictions in which the game will operate.