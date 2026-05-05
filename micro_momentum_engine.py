#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import threading
from datetime import datetime

import MetaTrader5 as mt5


class MicroMomentumEngine:
    """
    Lightweight tick-based micro-momentum layer.

    Rules:
    - It never produces standalone entries.
    - It only confirms the base direction or inverts it on a strong immediate reverse.
    """

    def __init__(
        self,
        log_callback=None,
        window_ticks=40,
        pressure_threshold=0.60,
        movement_min=0.05,
        ticks_per_second_min=6.0,
        micro_volatility_min=0.08,
        confirm_ticks=3,
    ):
        self.log_callback = log_callback
        self._lock = threading.Lock()

        self.window_ticks = max(10, int(window_ticks))
        self.pressure_threshold = float(pressure_threshold)
        self.movement_min = float(movement_min)
        self.ticks_per_second_min = float(ticks_per_second_min)
        self.micro_volatility_min = float(micro_volatility_min)
        self.confirm_ticks = max(1, int(confirm_ticks))

        self._last_reverse_direction = None
        self._reverse_streak = 0

    def log(self, message, msg_type="info"):
        if self.log_callback:
            try:
                self.log_callback(message, msg_type)
            except Exception:
                pass

    def update_params(
        self,
        window_ticks=None,
        pressure_threshold=None,
        movement_min=None,
        ticks_per_second_min=None,
        micro_volatility_min=None,
        confirm_ticks=None,
    ):
        with self._lock:
            if window_ticks is not None:
                self.window_ticks = max(10, int(window_ticks))
            if pressure_threshold is not None:
                self.pressure_threshold = float(pressure_threshold)
            if movement_min is not None:
                self.movement_min = float(movement_min)
            if ticks_per_second_min is not None:
                self.ticks_per_second_min = float(ticks_per_second_min)
            if micro_volatility_min is not None:
                self.micro_volatility_min = float(micro_volatility_min)
            if confirm_ticks is not None:
                self.confirm_ticks = max(1, int(confirm_ticks))

    def _extract_price(self, tick):
        last = float(tick.get("last", 0.0))
        if last > 0:
            return last
        bid = float(tick.get("bid", 0.0))
        ask = float(tick.get("ask", 0.0))
        if bid > 0 and ask > 0:
            return (bid + ask) / 2.0
        if bid > 0:
            return bid
        return ask

    def evaluate(self, symbol, predicted_direction):
        base_dir = (predicted_direction or "").upper()
        if base_dir not in ("BUY", "SELL"):
            return {
                "decision": "CONFIRM",
                "final_direction": base_dir,
                "reason": "Base direction invalid",
            }

        with self._lock:
            window_ticks = self.window_ticks
            pressure_threshold = self.pressure_threshold
            movement_min = self.movement_min
            tps_min = self.ticks_per_second_min
            vol_min = self.micro_volatility_min
            confirm_ticks = self.confirm_ticks

        ticks = mt5.copy_ticks_from(symbol, datetime.now(), int(window_ticks), mt5.COPY_TICKS_ALL)
        if ticks is None or len(ticks) < max(10, int(window_ticks * 0.5)):
            return {
                "decision": "CONFIRM",
                "final_direction": base_dir,
                "reason": "Insufficient ticks",
                "tick_count": int(0 if ticks is None else len(ticks)),
            }

        prices = []
        times_msc = []
        for t in ticks:
            p = self._extract_price(t)
            if p > 0:
                prices.append(p)
                times_msc.append(int(t.get("time_msc", 0)))

        if len(prices) < 8:
            return {
                "decision": "CONFIRM",
                "final_direction": base_dir,
                "reason": "Not enough priced ticks",
                "tick_count": len(prices),
            }

        up = 0
        down = 0
        for i in range(1, len(prices)):
            if prices[i] > prices[i - 1]:
                up += 1
            elif prices[i] < prices[i - 1]:
                down += 1

        directional = up + down
        buy_pressure = (up / directional) if directional > 0 else 0.5
        sell_pressure = (down / directional) if directional > 0 else 0.5

        movement = prices[-1] - prices[0]
        micro_volatility = max(prices) - min(prices)

        dt_seconds = 1.0
        if len(times_msc) >= 2 and times_msc[-1] > times_msc[0]:
            dt_seconds = max(0.001, (times_msc[-1] - times_msc[0]) / 1000.0)
        ticks_per_second = len(prices) / dt_seconds

        dominant_direction = "NONE"
        if buy_pressure >= pressure_threshold and movement >= movement_min:
            dominant_direction = "BUY"
        elif sell_pressure >= pressure_threshold and (-movement) >= movement_min:
            dominant_direction = "SELL"

        market_active = ticks_per_second >= tps_min and micro_volatility >= vol_min
        opposite_strong = market_active and dominant_direction in ("BUY", "SELL") and dominant_direction != base_dir

        if opposite_strong:
            if self._last_reverse_direction == dominant_direction:
                self._reverse_streak += 1
            else:
                self._last_reverse_direction = dominant_direction
                self._reverse_streak = 1
        else:
            self._last_reverse_direction = None
            self._reverse_streak = 0

        should_invert = opposite_strong and self._reverse_streak >= confirm_ticks
        final_direction = dominant_direction if should_invert else base_dir
        decision = "INVERT" if should_invert else "CONFIRM"

        return {
            "decision": decision,
            "final_direction": final_direction,
            "base_direction": base_dir,
            "dominant_direction": dominant_direction,
            "tick_count": len(prices),
            "up_ticks": up,
            "down_ticks": down,
            "buy_pressure": buy_pressure,
            "sell_pressure": sell_pressure,
            "movement": movement,
            "ticks_per_second": ticks_per_second,
            "micro_volatility": micro_volatility,
            "market_active": market_active,
            "reverse_streak": self._reverse_streak,
            "confirm_ticks": confirm_ticks,
            "reason": (
                f"{decision} | base={base_dir} dom={dominant_direction} "
                f"press(B/S)={buy_pressure:.2f}/{sell_pressure:.2f} "
                f"mv={movement:.3f} tps={ticks_per_second:.2f} vol={micro_volatility:.3f} "
                f"streak={self._reverse_streak}/{confirm_ticks}"
            ),
        }
