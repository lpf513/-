from __future__ import annotations

import hmac
from dataclasses import dataclass
from enum import Enum
from hashlib import sha256
from typing import Callable, Optional


class AdLifecycle(str, Enum):
    STARTED = "started"
    COMPLETED = "completed"
    SKIPPED = "skipped"
    ERROR = "error"


class PlatformError(str, Enum):
    NETWORK = "network_error"
    NO_FILL = "no_fill"
    USER_CANCEL = "user_cancel"
    UNKNOWN = "unknown"


@dataclass
class AdEvent:
    lifecycle: AdLifecycle
    placement_id: str
    error: PlatformError | None = None


@dataclass
class AdResult:
    completed: bool
    reward_granted: bool
    lifecycle: AdLifecycle
    reward_token: str = ""
    error: PlatformError | None = None


class RewardVerifier:
    """HMAC signature verifier for reward token.

    Token format: reward:<placement>:<signature_hex>
    where signature = HMAC_SHA256(secret, "reward:<placement>")
    """

    def __init__(self, secret: str = "dev-secret") -> None:
        self.secret = secret.encode("utf-8")

    def sign(self, payload: str) -> str:
        return hmac.new(self.secret, payload.encode("utf-8"), sha256).hexdigest()

    def verify(self, token: str) -> bool:
        parts = token.split(":")
        if len(parts) != 3 or parts[0] != "reward":
            return False
        payload = ":".join(parts[:2])
        expected = self.sign(payload)
        return hmac.compare_digest(expected, parts[2])


class RewardedAdAdapter:
    """SDK abstraction layer for future WeChat/other ad SDK integration."""

    def __init__(self, on_event: Optional[Callable[[AdEvent], None]] = None, verifier: RewardVerifier | None = None) -> None:
        self.on_event = on_event
        self.verifier = verifier or RewardVerifier()

    def show(self, placement_id: str, fail_once: bool = False) -> AdResult:
        self._emit(AdEvent(AdLifecycle.STARTED, placement_id))
        if fail_once:
            self._emit(AdEvent(AdLifecycle.ERROR, placement_id, PlatformError.NETWORK))
            return AdResult(
                completed=False,
                reward_granted=False,
                lifecycle=AdLifecycle.ERROR,
                error=PlatformError.NETWORK,
            )

        payload = f"reward:{placement_id}"
        token = f"{payload}:{self.verifier.sign(payload)}"
        verified = self.verifier.verify(token)
        result = AdResult(completed=True, reward_granted=verified, lifecycle=AdLifecycle.COMPLETED, reward_token=token)
        self._emit(AdEvent(result.lifecycle, placement_id))
        return result

    def show_with_retry(self, placement_id: str, max_retries: int = 2) -> AdResult:
        for retry in range(max_retries + 1):
            result = self.show(placement_id, fail_once=(retry == 0))
            if result.completed:
                return result
        return AdResult(completed=False, reward_granted=False, lifecycle=AdLifecycle.ERROR, error=PlatformError.UNKNOWN)

    @staticmethod
    def map_platform_error(error_code: int) -> PlatformError:
        return {
            1: PlatformError.NETWORK,
            2: PlatformError.NO_FILL,
            3: PlatformError.USER_CANCEL,
        }.get(error_code, PlatformError.UNKNOWN)

    def _emit(self, event: AdEvent) -> None:
        if self.on_event:
            self.on_event(event)
