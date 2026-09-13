package lottery

import (
	"fmt"
	"time"
)

type SettlementRecord struct {
	Key    SettlementKey
	Result TicketResult
}

func NewSettlementKey(ticket Ticket, draw Draw) SettlementKey {
	return SettlementKey{
		TicketID: ticket.ID,
		DrawID:   draw.ID,
	}
}

func SettleTicket(config GameConfig, ticket Ticket, draw Draw, existingSettlements map[SettlementKey]TicketResult, now time.Time) (TicketResult, bool, error) {
	if draw.Status != DrawStatusResultGenerated {
		return TicketResult{}, false, fmt.Errorf("draw must be %s to settle tickets", DrawStatusResultGenerated)
	}

	if ticket.DrawID != draw.ID {
		return TicketResult{}, false, fmt.Errorf("ticket draw id %s does not match draw id %s", ticket.DrawID, draw.ID)
	}

	key := NewSettlementKey(ticket, draw)
	if existingResult, ok := existingSettlements[key]; ok {
		return existingResult, false, nil
	}

	matchResult, err := MatchTicket(config, ticket, draw)
	if err != nil {
		return TicketResult{}, false, err
	}

	reward := CalculateReward(config, matchResult)
	outcome := TicketOutcomeLose
	if reward > 0 {
		outcome = TicketOutcomeWin
	}

	result := TicketResult{
		ID:                key.TicketID + ":" + key.DrawID,
		TicketID:          ticket.ID,
		DrawID:            draw.ID,
		PrimaryMatchCount: matchResult.PrimaryMatchCount,
		PowerMatch:        matchResult.PowerMatch,
		Reward:            reward,
		Outcome:           outcome,
		SettledAt:         now,
	}

	if existingSettlements != nil {
		existingSettlements[key] = result
	}

	return result, true, nil
}
