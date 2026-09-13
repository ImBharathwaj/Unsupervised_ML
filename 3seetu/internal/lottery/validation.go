package lottery

import "fmt"

func ValidateConfig(config GameConfig) error {
	if config.Digits <= 0 {
		return fmt.Errorf("digits must be greater than zero")
	}

	if config.PowerDigits < 0 {
		return fmt.Errorf("power digits cannot be negative")
	}

	if config.PowerDigits > 1 {
		return fmt.Errorf("only zero or one power digit is currently supported")
	}

	if config.EntryPrice < 0 {
		return fmt.Errorf("entry price cannot be negative")
	}

	if config.MatchRule != MatchRulePrefix {
		return fmt.Errorf("unsupported match rule: %s", config.MatchRule)
	}

	for _, tier := range config.PrizeTiers {
		if tier.PrimaryMatches < 0 || tier.PrimaryMatches > config.Digits {
			return fmt.Errorf("invalid prize tier primary match count: %d", tier.PrimaryMatches)
		}

		if tier.Reward < 0 {
			return fmt.Errorf("prize tier reward cannot be negative")
		}
	}

	return nil
}

func ValidateSelection(config GameConfig, numbers []int, powerNumber *int) error {
	if err := ValidateConfig(config); err != nil {
		return err
	}

	if len(numbers) != config.Digits {
		return fmt.Errorf("expected %d numbers, got %d", config.Digits, len(numbers))
	}

	for index, digit := range numbers {
		if !isSingleDigit(digit) {
			return fmt.Errorf("number at position %d must be between 0 and 9", index)
		}
	}

	if config.PowerDigits == 0 && powerNumber != nil {
		return fmt.Errorf("power number is not allowed for this game")
	}

	if config.PowerDigits == 1 {
		if powerNumber == nil {
			return fmt.Errorf("power number is required")
		}

		if !isSingleDigit(*powerNumber) {
			return fmt.Errorf("power number must be between 0 and 9")
		}
	}

	return nil
}

func isSingleDigit(value int) bool {
	return value >= 0 && value <= 9
}
