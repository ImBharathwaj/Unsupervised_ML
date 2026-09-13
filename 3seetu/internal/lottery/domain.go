package lottery

import (
	"time"
)

type GameType string

const (
	GameTypeThreeDigit     GameType = "THREE_DIGIT"
	GameTypeFiveDigit      GameType = "FIVE_DIGIT"
	GameTypeFiveDigitPower GameType = "FIVE_DIGIT_POWER"
)

type DrawStatus string

const (
	DrawStatusScheduled       DrawStatus = "SCHEDULED"
	DrawStatusOpen            DrawStatus = "OPEN"
	DrawStatusClosed          DrawStatus = "CLOSED"
	DrawStatusDrawing         DrawStatus = "DRAWING"
	DrawStatusResultGenerated DrawStatus = "RESULT_GENERATED"
	DrawStatusSettled         DrawStatus = "SETTLED"
)

type TicketStatus string

const (
	TicketStatusPending TicketStatus = "PENDING"
	TicketStatusSettled TicketStatus = "SETTLED"
)

type TicketOutcome string

const (
	TicketOutcomeWin  TicketOutcome = "WIN"
	TicketOutcomeLose TicketOutcome = "LOSE"
)

type MatchRule string

const (
	MatchRulePrefix MatchRule = "PREFIX"
)

type AuditEventType string

const (
	AuditEventDrawCreated            AuditEventType = "DRAW_CREATED"
	AuditEventDrawOpened             AuditEventType = "DRAW_OPENED"
	AuditEventTicketCreated          AuditEventType = "TICKET_CREATED"
	AuditEventWalletDebited          AuditEventType = "WALLET_DEBITED"
	AuditEventDrawClosed             AuditEventType = "DRAW_CLOSED"
	AuditEventWinningNumberGenerated AuditEventType = "WINNING_NUMBER_GENERATED"
	AuditEventResultPublished        AuditEventType = "RESULT_PUBLISHED"
	AuditEventTicketSettled          AuditEventType = "TICKET_SETTLED"
	AuditEventRewardCredited         AuditEventType = "REWARD_CREDITED"
)

type PrizeTier struct {
	PrimaryMatches int
	PowerMatch     *bool
	Reward         int64
}

type GameConfig struct {
	GameType    GameType
	Digits      int
	PowerDigits int
	EntryPrice  int64
	MatchRule   MatchRule
	PrizeTiers  []PrizeTier
}

type Game struct {
	ID        string
	Name      string
	Type      GameType
	Status    string
	Config    GameConfig
	CreatedAt time.Time
}

type Draw struct {
	ID                 string
	GameID             string
	WinningNumbers     []int
	WinningPowerNumber *int
	Status             DrawStatus
	OpenedAt           *time.Time
	ClosedAt           *time.Time
	DrawnAt            *time.Time
	SettledAt          *time.Time
}

type Ticket struct {
	ID          string
	DrawID      string
	UserID      string
	Numbers     []int
	PowerNumber *int
	EntryPrice  int64
	Status      TicketStatus
	CreatedAt   time.Time
}

type MatchResult struct {
	PrimaryMatchCount int
	PowerMatch        bool
}

type TicketResult struct {
	ID                string
	TicketID          string
	DrawID            string
	PrimaryMatchCount int
	PowerMatch        bool
	Reward            int64
	Outcome           TicketOutcome
	SettledAt         time.Time
}

type SettlementKey struct {
	TicketID string
	DrawID   string
}

type AuditEvent struct {
	ID         string
	Type       AuditEventType
	EntityID   string
	ActorID    string
	OccurredAt time.Time
	Metadata   map[string]string
}
