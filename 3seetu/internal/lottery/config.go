package lottery

func BoolPtr(value bool) *bool {
	return &value
}

func ThreeDigitConfig() GameConfig {
	return GameConfig{
		GameType:    GameTypeThreeDigit,
		Digits:      3,
		PowerDigits: 0,
		EntryPrice:  120,
		MatchRule:   MatchRulePrefix,
		PrizeTiers: []PrizeTier{
			{PrimaryMatches: 3, Reward: 25000},
			{PrimaryMatches: 2, Reward: 1000},
			{PrimaryMatches: 1, Reward: 120},
		},
	}
}
