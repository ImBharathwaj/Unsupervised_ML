package lottery

import "fmt"

func MatchTicket(config GameConfig, ticket Ticket, draw Draw) (MatchResult, error) {
	if err := ValidateSelection(config, ticket.Numbers, ticket.PowerNumber); err != nil {
		return MatchResult{}, fmt.Errorf("invalid ticket selection: %w", err)
	}

	if err := ValidateSelection(config, draw.WinningNumbers, draw.WinningPowerNumber); err != nil {
		return MatchResult{}, fmt.Errorf("invalid draw result: %w", err)
	}

	switch config.MatchRule {
	case MatchRulePrefix:
		return MatchResult{
			PrimaryMatchCount: prefixMatchCount(ticket.Numbers, draw.WinningNumbers),
			PowerMatch:        powerMatches(ticket.PowerNumber, draw.WinningPowerNumber),
		}, nil
	default:
		return MatchResult{}, fmt.Errorf("unsupported match rule: %s", config.MatchRule)
	}
}

func prefixMatchCount(playerNumbers []int, winningNumbers []int) int {
	matchCount := 0

	for index := range playerNumbers {
		if playerNumbers[index] != winningNumbers[index] {
			break
		}

		matchCount++
	}

	return matchCount
}

func powerMatches(playerPower *int, winningPower *int) bool {
	return playerPower != nil && winningPower != nil && *playerPower == *winningPower
}
