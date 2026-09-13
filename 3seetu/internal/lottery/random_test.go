package lottery

import "testing"

func TestGenerateWinningResultUsesConfiguredShape(t *testing.T) {
	t.Parallel()

	numbers, powerNumber, err := GenerateWinningResult(ThreeDigitConfig())
	if err != nil {
		t.Fatalf("GenerateWinningResult() error = %v", err)
	}

	if len(numbers) != 3 {
		t.Fatalf("len(numbers) = %d, want 3", len(numbers))
	}

	if powerNumber != nil {
		t.Fatal("powerNumber != nil, want nil")
	}

	for _, digit := range numbers {
		if digit < 0 || digit > 9 {
			t.Fatalf("digit = %d, want 0-9", digit)
		}
	}
}
