package lottery

import (
	"testing"
	"time"
)

func TestNewAuditEventDefaultsMetadata(t *testing.T) {
	t.Parallel()

	now := time.Date(2026, 9, 13, 12, 0, 0, 0, time.UTC)
	event := NewAuditEvent("event-1", AuditEventTicketSettled, "ticket-1", "worker-1", now, nil)

	if event.ID != "event-1" {
		t.Fatalf("ID = %s, want event-1", event.ID)
	}
	if event.Type != AuditEventTicketSettled {
		t.Fatalf("Type = %s, want %s", event.Type, AuditEventTicketSettled)
	}
	if event.Metadata == nil {
		t.Fatal("Metadata = nil, want empty map")
	}
}
