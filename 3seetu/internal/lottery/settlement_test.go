package lottery

import (
	"testing"
	"time"
)

func TestSettleTicketCreatesResultOnce(t *testing.T) {
	t.Parallel()

	config := ThreeDigitConfig()
	now := time.Date(2026, 9, 13, 12, 0, 0, 0, time.UTC)
	draw := Draw{
		ID:             "draw-1",
		GameID:         "game-1",
		WinningNumbers: []int{4, 7, 2},
		Status:         DrawStatusResultGenerated,
	}
	ticket := Ticket{
		ID:         "ticket-1",
		DrawID:     draw.ID,
		UserID:     "user-1",
		Numbers:    []int{4, 7, 2},
		EntryPrice: config.EntryPrice,
		Status:     TicketStatusPending,
	}
	settlements := map[SettlementKey]TicketResult{}

	result, created, err := SettleTicket(config, ticket, draw, settlements, now)
	if err != nil {
		t.Fatalf("SettleTicket() error = %v", err)
	}
	if !created {
		t.Fatal("created = false, want true")
	}
	if result.Reward != 25000 || result.Outcome != TicketOutcomeWin {
		t.Fatalf("result = %+v, want winning reward", result)
	}

	duplicateResult, duplicateCreated, err := SettleTicket(config, ticket, draw, settlements, now.Add(time.Hour))
	if err != nil {
		t.Fatalf("duplicate SettleTicket() error = %v", err)
	}
	if duplicateCreated {
		t.Fatal("duplicateCreated = true, want false")
	}
	if duplicateResult != result {
		t.Fatalf("duplicateResult = %+v, want %+v", duplicateResult, result)
	}
}

func TestSettleTicketRequiresGeneratedResult(t *testing.T) {
	t.Parallel()

	_, _, err := SettleTicket(ThreeDigitConfig(), Ticket{DrawID: "draw-1"}, Draw{ID: "draw-1", Status: DrawStatusDrawing}, nil, time.Now())
	if err == nil {
		t.Fatal("SettleTicket() error = nil, want error")
	}
}

func TestSettleTicketRejectsDrawMismatch(t *testing.T) {
	t.Parallel()

	_, _, err := SettleTicket(ThreeDigitConfig(), Ticket{DrawID: "draw-2"}, Draw{ID: "draw-1", Status: DrawStatusResultGenerated}, nil, time.Now())
	if err == nil {
		t.Fatal("SettleTicket() error = nil, want error")
	}
}
