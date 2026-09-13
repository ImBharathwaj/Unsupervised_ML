package lottery

func CalculateReward(config GameConfig, result MatchResult) int64 {
	for _, tier := range config.PrizeTiers {
		if tier.PrimaryMatches != result.PrimaryMatchCount {
			continue
		}

		if tier.PowerMatch != nil && *tier.PowerMatch != result.PowerMatch {
			continue
		}

		return tier.Reward
	}

	return 0
}
