package lottery

import (
	"crypto/rand"
	"fmt"
	"math/big"
)

func GenerateDigits(count int) ([]int, error) {
	if count <= 0 {
		return nil, fmt.Errorf("digit count must be greater than zero")
	}

	digits := make([]int, count)
	for index := range digits {
		value, err := rand.Int(rand.Reader, big.NewInt(10))
		if err != nil {
			return nil, fmt.Errorf("generate secure digit: %w", err)
		}

		digits[index] = int(value.Int64())
	}

	return digits, nil
}

func GenerateWinningResult(config GameConfig) ([]int, *int, error) {
	if err := ValidateConfig(config); err != nil {
		return nil, nil, err
	}

	numbers, err := GenerateDigits(config.Digits)
	if err != nil {
		return nil, nil, err
	}

	if config.PowerDigits == 0 {
		return numbers, nil, nil
	}

	powerDigits, err := GenerateDigits(config.PowerDigits)
	if err != nil {
		return nil, nil, err
	}

	return numbers, &powerDigits[0], nil
}
