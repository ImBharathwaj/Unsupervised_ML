package lottery

import "testing"

func TestApplyTransactionsCalculatesLedgerBalance(t *testing.T) {
	t.Parallel()

	balance, err := ApplyTransactions([]WalletTransaction{
		{Type: WalletTransactionPromotionalCredit, Amount: 1000},
		{Type: WalletTransactionTicketPurchase, Amount: -120},
		{Type: WalletTransactionWinningReward, Amount: 25000},
	})
	if err != nil {
		t.Fatalf("ApplyTransactions() error = %v", err)
	}

	if balance != 25880 {
		t.Fatalf("balance = %d, want 25880", balance)
	}
}

func TestApplyTransactionsRejectsNegativeBalance(t *testing.T) {
	t.Parallel()

	_, err := ApplyTransactions([]WalletTransaction{
		{Type: WalletTransactionTicketPurchase, Amount: -120},
	})
	if err == nil {
		t.Fatal("ApplyTransactions() error = nil, want error")
	}
}
