package lottery

import (
	"testing"
	"time"
)

func TestTransitionDrawFollowsStrictLifecycle(t *testing.T) {
	t.Parallel()

	now := time.Date(2026, 9, 13, 10, 0, 0, 0, time.UTC)
	draw := Draw{ID: "draw-1", Status: DrawStatusScheduled}

	var err error
	draw, err = TransitionDraw(draw, DrawStatusOpen, now)
	if err != nil {
		t.Fatalf("TransitionDraw(open) error = %v", err)
	}
	if draw.Status != DrawStatusOpen || draw.OpenedAt == nil {
		t.Fatalf("draw after open = %+v", draw)
	}

	draw, err = TransitionDraw(draw, DrawStatusClosed, now)
	if err != nil {
		t.Fatalf("TransitionDraw(closed) error = %v", err)
	}
	if draw.Status != DrawStatusClosed || draw.ClosedAt == nil {
		t.Fatalf("draw after close = %+v", draw)
	}

	draw, err = TransitionDraw(draw, DrawStatusDrawing, now)
	if err != nil {
		t.Fatalf("TransitionDraw(drawing) error = %v", err)
	}

	draw, err = TransitionDraw(draw, DrawStatusResultGenerated, now)
	if err != nil {
		t.Fatalf("TransitionDraw(result generated) error = %v", err)
	}
	if draw.Status != DrawStatusResultGenerated || draw.DrawnAt == nil {
		t.Fatalf("draw after result generated = %+v", draw)
	}

	draw, err = TransitionDraw(draw, DrawStatusSettled, now)
	if err != nil {
		t.Fatalf("TransitionDraw(settled) error = %v", err)
	}
	if draw.Status != DrawStatusSettled || draw.SettledAt == nil {
		t.Fatalf("draw after settled = %+v", draw)
	}
}

func TestTransitionDrawRejectsSkippedStates(t *testing.T) {
	t.Parallel()

	_, err := TransitionDraw(Draw{Status: DrawStatusOpen}, DrawStatusDrawing, time.Now())
	if err == nil {
		t.Fatal("TransitionDraw() error = nil, want error")
	}
}

func TestDrawStateGuards(t *testing.T) {
	t.Parallel()

	if !CanPurchaseTicket(Draw{Status: DrawStatusOpen}) {
		t.Fatal("CanPurchaseTicket(open) = false, want true")
	}
	if CanPurchaseTicket(Draw{Status: DrawStatusClosed}) {
		t.Fatal("CanPurchaseTicket(closed) = true, want false")
	}
	if !CanGenerateResult(Draw{Status: DrawStatusDrawing}) {
		t.Fatal("CanGenerateResult(drawing) = false, want true")
	}
	if !CanSettleDraw(Draw{Status: DrawStatusResultGenerated}) {
		t.Fatal("CanSettleDraw(result generated) = false, want true")
	}
}
