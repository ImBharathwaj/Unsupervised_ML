package lottery

import (
	"fmt"
	"time"
)

type WalletTransactionType string

const (
	WalletTransactionPromotionalCredit WalletTransactionType = "PROMOTIONAL_CREDIT"
	WalletTransactionTicketPurchase    WalletTransactionType = "TICKET_PURCHASE"
	WalletTransactionWinningReward     WalletTransactionType = "WINNING_REWARD"
)

type WalletTransaction struct {
	ID            string
	UserID        string
	Type          WalletTransactionType
	Amount        int64
	ReferenceType string
	ReferenceID   string
	CreatedAt     time.Time
}

func ApplyTransactions(transactions []WalletTransaction) (int64, error) {
	var balance int64

	for _, transaction := range transactions {
		if transaction.Amount == 0 {
			return 0, fmt.Errorf("wallet transaction amount cannot be zero")
		}

		balance += transaction.Amount
		if balance < 0 {
			return 0, fmt.Errorf("wallet balance cannot go negative")
		}
	}

	return balance, nil
}
