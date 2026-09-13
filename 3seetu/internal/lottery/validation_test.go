package lottery

import "testing"

func TestValidateSelectionAllowsLeadingZeroes(t *testing.T) {
	t.Parallel()

	if err := ValidateSelection(ThreeDigitConfig(), []int{0, 0, 7}, nil); err != nil {
		t.Fatalf("ValidateSelection() error = %v", err)
	}
}

func TestValidateSelectionRejectsWrongDigitCount(t *testing.T) {
	t.Parallel()

	err := ValidateSelection(ThreeDigitConfig(), []int{4, 7}, nil)
	if err == nil {
		t.Fatal("ValidateSelection() error = nil, want error")
	}
}

func TestValidateSelectionRejectsNonDigits(t *testing.T) {
	t.Parallel()

	err := ValidateSelection(ThreeDigitConfig(), []int{4, 10, 2}, nil)
	if err == nil {
		t.Fatal("ValidateSelection() error = nil, want error")
	}
}

func TestValidateSelectionRequiresPowerDigit(t *testing.T) {
	t.Parallel()

	config := GameConfig{
		GameType:    GameTypeFiveDigitPower,
		Digits:      5,
		PowerDigits: 1,
		EntryPrice:  200,
		MatchRule:   MatchRulePrefix,
	}

	err := ValidateSelection(config, []int{4, 7, 2, 8, 1}, nil)
	if err == nil {
		t.Fatal("ValidateSelection() error = nil, want error")
	}
}
