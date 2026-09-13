package lottery

import "testing"

func TestThreeDigitPrefixMatchingAndPrize(t *testing.T) {
	t.Parallel()

	config := ThreeDigitConfig()
	draw := Draw{
		ID:             "draw-1",
		GameID:         "game-1",
		WinningNumbers: []int{4, 7, 2},
		Status:         DrawStatusResultGenerated,
	}

	tests := []struct {
		name            string
		playerNumbers   []int
		expectedMatches int
		expectedReward  int64
	}{
		{name: "three prefix matches", playerNumbers: []int{4, 7, 2}, expectedMatches: 3, expectedReward: 25000},
		{name: "two prefix matches with final miss", playerNumbers: []int{4, 7, 1}, expectedMatches: 2, expectedReward: 1000},
		{name: "two prefix matches with different final miss", playerNumbers: []int{4, 7, 9}, expectedMatches: 2, expectedReward: 1000},
		{name: "one prefix match with later positional match ignored", playerNumbers: []int{4, 9, 2}, expectedMatches: 1, expectedReward: 120},
		{name: "zero prefix matches", playerNumbers: []int{1, 7, 2}, expectedMatches: 0, expectedReward: 0},
		{name: "unordered digits do not win", playerNumbers: []int{7, 4, 2}, expectedMatches: 0, expectedReward: 0},
		{name: "all zeroes do not match", playerNumbers: []int{0, 0, 0}, expectedMatches: 0, expectedReward: 0},
	}

	for _, test := range tests {
		test := test
		t.Run(test.name, func(t *testing.T) {
			t.Parallel()

			ticket := Ticket{
				ID:         "ticket-1",
				DrawID:     draw.ID,
				UserID:     "user-1",
				Numbers:    test.playerNumbers,
				EntryPrice: config.EntryPrice,
				Status:     TicketStatusPending,
			}

			result, err := MatchTicket(config, ticket, draw)
			if err != nil {
				t.Fatalf("MatchTicket() error = %v", err)
			}

			if result.PrimaryMatchCount != test.expectedMatches {
				t.Fatalf("PrimaryMatchCount = %d, want %d", result.PrimaryMatchCount, test.expectedMatches)
			}

			reward := CalculateReward(config, result)
			if reward != test.expectedReward {
				t.Fatalf("CalculateReward() = %d, want %d", reward, test.expectedReward)
			}
		})
	}
}

func TestPowerDigitMatching(t *testing.T) {
	t.Parallel()

	config := GameConfig{
		GameType:    GameTypeFiveDigitPower,
		Digits:      5,
		PowerDigits: 1,
		EntryPrice:  200,
		MatchRule:   MatchRulePrefix,
		PrizeTiers: []PrizeTier{
			{PrimaryMatches: 3, PowerMatch: BoolPtr(true), Reward: 500},
		},
	}

	playerPower := 6
	winningPower := 6
	result, err := MatchTicket(config, Ticket{
		Numbers:     []int{4, 7, 2, 8, 1},
		PowerNumber: &playerPower,
	}, Draw{
		WinningNumbers:     []int{4, 7, 2, 9, 5},
		WinningPowerNumber: &winningPower,
	})
	if err != nil {
		t.Fatalf("MatchTicket() error = %v", err)
	}

	if result.PrimaryMatchCount != 3 {
		t.Fatalf("PrimaryMatchCount = %d, want 3", result.PrimaryMatchCount)
	}

	if !result.PowerMatch {
		t.Fatal("PowerMatch = false, want true")
	}

	if reward := CalculateReward(config, result); reward != 500 {
		t.Fatalf("CalculateReward() = %d, want 500", reward)
	}
}
