package lottery

import "time"

func NewAuditEvent(id string, eventType AuditEventType, entityID string, actorID string, now time.Time, metadata map[string]string) AuditEvent {
	if metadata == nil {
		metadata = map[string]string{}
	}

	return AuditEvent{
		ID:         id,
		Type:       eventType,
		EntityID:   entityID,
		ActorID:    actorID,
		OccurredAt: now,
		Metadata:   metadata,
	}
}
