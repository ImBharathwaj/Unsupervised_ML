package lottery

import (
	"fmt"
	"time"
)

var allowedDrawTransitions = map[DrawStatus]map[DrawStatus]bool{
	DrawStatusScheduled: {
		DrawStatusOpen: true,
	},
	DrawStatusOpen: {
		DrawStatusClosed: true,
	},
	DrawStatusClosed: {
		DrawStatusDrawing: true,
	},
	DrawStatusDrawing: {
		DrawStatusResultGenerated: true,
	},
	DrawStatusResultGenerated: {
		DrawStatusSettled: true,
	},
}

func TransitionDraw(draw Draw, nextStatus DrawStatus, now time.Time) (Draw, error) {
	if draw.Status == nextStatus {
		return draw, nil
	}

	if !allowedDrawTransitions[draw.Status][nextStatus] {
		return Draw{}, fmt.Errorf("invalid draw transition from %s to %s", draw.Status, nextStatus)
	}

	draw.Status = nextStatus

	switch nextStatus {
	case DrawStatusOpen:
		draw.OpenedAt = &now
	case DrawStatusClosed:
		draw.ClosedAt = &now
	case DrawStatusResultGenerated:
		draw.DrawnAt = &now
	case DrawStatusSettled:
		draw.SettledAt = &now
	}

	return draw, nil
}

func CanPurchaseTicket(draw Draw) bool {
	return draw.Status == DrawStatusOpen
}

func CanGenerateResult(draw Draw) bool {
	return draw.Status == DrawStatusDrawing
}

func CanSettleDraw(draw Draw) bool {
	return draw.Status == DrawStatusResultGenerated
}
