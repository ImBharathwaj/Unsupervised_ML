# Lottery System

Configurable virtual-credit lottery game system.

The application is being built around one reusable engine where game rules live in configuration. The first target game is the 3-digit lottery with positional prefix matching.

## Current Status

Phase 1: Core Domain MVP is implemented and under test.

## Phase 1: Core Domain MVP

### Done

- Created Go backend module.
- Added core domain models:
  - `Game`
  - `GameConfig`
  - `Draw`
  - `Ticket`
  - `TicketResult`
  - `PrizeTier`
  - `WalletTransaction`
  - `AuditEvent`
- Added configurable 3-digit game setup:
  - 3 digits
  - 120 credit entry price
  - 25,000 reward for 3 prefix matches
  - 1,000 reward for 2 prefix matches
  - 120 reward for 1 prefix match
- Added number validation:
  - Correct digit count
  - Digits must be `0-9`
  - Leading zeroes are allowed
  - Power digit support is validated for future game types
- Added generic prefix match engine.
- Added power digit match support.
- Added prize engine separated from matching.
- Added cryptographically secure digit generation using `crypto/rand`.
- Added draw lifecycle transition helpers:
  - `SCHEDULED -> OPEN`
  - `OPEN -> CLOSED`
  - `CLOSED -> DRAWING`
  - `DRAWING -> RESULT_GENERATED`
  - `RESULT_GENERATED -> SETTLED`
- Added draw state guards for purchasing, result generation, and settlement.
- Added settlement helper that evaluates a ticket and calculates reward.
- Added settlement idempotency model using `SettlementKey` with `ticket_id + draw_id` semantics.
- Added audit event model and constructor.
- Added wallet ledger balance calculation using integer credits.
- Added unit tests for:
  - 3-digit prefix matching
  - 3-digit prize calculation
  - Leading zero validation
  - Invalid selection validation
  - Power digit matching
  - Secure result shape
  - Draw lifecycle transitions
  - Invalid skipped lifecycle transitions
  - Draw state guards
  - Ticket settlement
  - Duplicate settlement prevention
  - Settlement state validation
  - Audit event creation
  - Wallet ledger balance
  - Negative wallet balance rejection

### Not Done Yet

- No database persistence yet.
- No PostgreSQL migrations yet.
- No HTTP API yet.
- No user authentication yet.
- No ticket purchase transaction workflow yet.
- No persistent wallet debit or credit transaction storage yet.
- No background worker yet.
- No frontend yet.
- No admin dashboard yet.

## Phase 2: 3-Digit Complete Game

### Next Tasks

- Add ticket purchase workflow.
- Require draw status to be `OPEN` before purchase.
- Validate user selection against game config.
- Debit wallet through ledger transaction.
- Create ticket record through repository interface.
- Add draw result generation workflow.
- Generate winning numbers only after draw enters `DRAWING`.
- Persist immutable draw result through repository interface.
- Add settlement workflow for all draw tickets.
- Credit rewards through wallet transactions.
- Add application-level tests for purchase, result generation, and settlement.

## Phase 3: Persistence

### Planned

- Add PostgreSQL migrations.
- Add repository interfaces and PostgreSQL implementations.
- Add database transaction handling.
- Add unique settlement constraint for `(ticket_id, draw_id)`.
- Add audit log table.

## Phase 4: API

### Planned

- `GET /api/v1/games`
- `GET /api/v1/games/{gameId}`
- `POST /api/v1/draws/{drawId}/tickets`
- `GET /api/v1/draws/{drawId}/result`
- `GET /api/v1/tickets/{ticketId}/result`

## Phase 5: Admin

### Planned

- Manage games.
- Configure prize tiers.
- Schedule, open, close, and draw results.
- View tickets, winners, credit transactions, and audit logs.
- Prevent modification of completed draw results.

## Phase 6: Frontend

### Planned

- Player flow for choosing a game, selecting digits, purchasing tickets, and viewing results.
- Admin flow for managing games, draws, settlements, and audits.

## Rules To Preserve

- Winning numbers are generated only on the server.
- Winning numbers are generated after a draw closes.
- Winning number generation must not inspect player tickets.
- Matching is positional and prefix-based for the 3-digit game.
- Leading zeroes must remain valid.
- Credits are integer values, not floats.
- Wallet changes must use ledger transactions.
- Settlement must be idempotent.
- Game rules belong in configuration; the engine should stay generic.

## Validation

Run the test suite:

```bash
go test ./...
```
