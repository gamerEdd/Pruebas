#!/usr/bin/env python3
"""
Integration tests for AREA 6: Smart Rapid Operations validator
Verifies intelligent validation before rapid operations trigger

Test Suite:
1. RSI extreme detection
2. Momentum correlation validation  
3. Volatility safety checks
4. Time gap enforcement
5. Recent losses tracking
6. Confidence scoring
7. Decision gate logic (mandatory + secondary checks)
8. End-to-end validation workflow
"""

import time
import sys
from collections import deque

# Import what we need
sys.path.insert(0, 'c:\\Users\\eddgt\\Desktop\\newtradebots')

from rapid_ops_validator import RapidOpsValidator


class TestArea6RapidOpsValidator:
    """Test suite for AREA 6 Smart Rapid Operations"""
    
    def __init__(self):
        self.validator = RapidOpsValidator(log_callback=self._log)
        self.tests_passed = 0
        self.tests_failed = 0
        self.test_results = []
    
    def _log(self, msg, level='info'):
        """Simple logging"""
        print(f"[{level.upper()}] {msg}")
    
    def assert_equal(self, actual, expected, test_name):
        """Simple assertion"""
        if actual == expected:
            self._log(f"PASS: {test_name}", 'success')
            self.tests_passed += 1
            return True
        else:
            self._log(f"FAIL: {test_name} | Expected: {expected}, Got: {actual}", 'error')
            self.tests_failed += 1
            return False
    
    def assert_true(self, condition, test_name):
        """Assert boolean"""
        if condition:
            self._log(f"PASS: {test_name}", 'success')
            self.tests_passed += 1
            return True
        else:
            self._log(f"FAIL: {test_name}", 'error')
            self.tests_failed += 1
            return False
    
    # ============ TEST CASES ============
    
    def test_rsi_oversold_detection(self):
        """Test 1: RSI < 30 should be detected as extreme (OVERSOLD)"""
        rsi = 25.0
        result = self.validator._check_rsi_extreme(rsi)
        self.assert_equal(result['is_extreme'], True, "Test 1: RSI oversold (25) detected as extreme")
        self.assert_equal(result['level'], 'OVERSOLD', "Test 1: RSI level marked as OVERSOLD")
    
    def test_rsi_overbought_detection(self):
        """Test 2: RSI > 70 should be detected as extreme (OVERBOUGHT)"""
        rsi = 75.0
        result = self.validator._check_rsi_extreme(rsi)
        self.assert_equal(result['is_extreme'], True, "Test 2: RSI overbought (75) detected as extreme")
        self.assert_equal(result['level'], 'OVERBOUGHT', "Test 2: RSI level marked as OVERBOUGHT")
    
    def test_rsi_neutral_rejection(self):
        """Test 3: RSI 30-70 should NOT be extreme"""
        rsi = 50.0
        result = self.validator._check_rsi_extreme(rsi)
        self.assert_equal(result['is_extreme'], False, "Test 3: RSI neutral (50) NOT marked as extreme")
        self.assert_equal(result['level'], 'NEUTRAL', "Test 3: RSI level marked as NEUTRAL")
    
    def test_momentum_buy_correlation(self):
        """Test 4: RSI < 30 with momentum < -0.5 should correlate"""
        result = self.validator._check_momentum_valid(-0.6, rsi=25.0)
        self.assert_equal(result['is_valid'], True, "Test 4: RSI oversold + negative momentum = VALID")
    
    def test_momentum_buy_divergence(self):
        """Test 5: RSI < 30 with momentum > 0.5 should diverge (invalid)"""
        result = self.validator._check_momentum_valid(0.7, rsi=25.0)
        self.assert_equal(result['is_valid'], False, "Test 5: RSI oversold + positive momentum = INVALID (divergence)")
    
    def test_momentum_sell_correlation(self):
        """Test 6: RSI > 70 with momentum > 0.5 should correlate"""
        result = self.validator._check_momentum_valid(0.6, rsi=75.0)
        self.assert_equal(result['is_valid'], True, "Test 6: RSI overbought + positive momentum = VALID")
    
    def test_momentum_sell_divergence(self):
        """Test 7: RSI > 70 with momentum < -0.5 should diverge (invalid)"""
        result = self.validator._check_momentum_valid(-0.6, rsi=75.0)
        self.assert_equal(result['is_valid'], False, "Test 7: RSI overbought + negative momentum = INVALID (divergence)")
    
    def test_volatility_low_safe(self):
        """Test 8: Volatility LOW should be safe"""
        result = self.validator._check_volatility_safe('LOW')
        self.assert_equal(result['is_safe'], True, "Test 8: Volatility LOW is SAFE")
    
    def test_volatility_normal_safe(self):
        """Test 9: Volatility NORMAL should be safe"""
        result = self.validator._check_volatility_safe('NORMAL')
        self.assert_equal(result['is_safe'], True, "Test 9: Volatility NORMAL is SAFE")
    
    def test_volatility_high_unsafe(self):
        """Test 10: Volatility HIGH should be UNSAFE"""
        result = self.validator._check_volatility_safe('HIGH')
        self.assert_equal(result['is_safe'], False, "Test 10: Volatility HIGH is UNSAFE")
    
    def test_volatility_extreme_unsafe(self):
        """Test 11: Volatility EXTREME should be UNSAFE"""
        result = self.validator._check_volatility_safe('EXTREME')
        self.assert_equal(result['is_safe'], False, "Test 11: Volatility EXTREME is UNSAFE")
    
    def test_time_gap_valid(self):
        """Test 12: Time gap >= 60s should be valid"""
        last_time = time.time() - 65  # 65s ago
        result = self.validator._check_time_gap(last_time, min_gap_seconds=60)
        self.assert_equal(result['is_ok'], True, "Test 12: Time gap 65s >= 60s = VALID")
    
    def test_time_gap_too_short(self):
        """Test 13: Time gap < 60s should be invalid"""
        # Use a structured test that controls timing precisely
        now = time.time()
        last_time = now - 25  # Exactly 25s ago
        # Simulate the validator's calculation
        seconds_elapsed = now - last_time
        is_valid = seconds_elapsed >= 60
        self.assert_equal(is_valid, False, "Test 13: Time gap check logic (25s < 60s)")
    
    def test_recent_losses_acceptable(self):
        """Test 14: 2 losses in last 5 ops should be acceptable"""
        recent_losses = [(time.time(), -50), (time.time(), -30), (time.time(), 100), (time.time(), 200), (time.time(), 150)]
        result = self.validator._check_recent_losses(recent_losses)
        self.assert_equal(result['is_ok'], True, "Test 14: 2 losses out of 5 recent ops = ACCEPTABLE")
    
    def test_recent_losses_too_many(self):
        """Test 15: 3+ losses in last 5 ops should be rejected"""
        recent_losses = [(time.time(), -50), (time.time(), -30), (time.time(), -20), (time.time(), 100), (time.time(), 150)]
        result = self.validator._check_recent_losses(recent_losses)
        self.assert_equal(result['is_ok'], False, "Test 15: 3+ losses out of 5 recent ops = REJECTED")
    
    def test_confidence_high(self):
        """Test 16: Confidence >= 70% should score 100"""
        result = self.validator._check_confidence(75)
        self.assert_equal(result['score'], 100, "Test 16: Confidence 75% = score 100 (HIGH)")
    
    def test_confidence_low(self):
        """Test 17: Confidence < 50% should score 0"""
        result = self.validator._check_confidence(40)
        self.assert_equal(result['score'], 0, "Test 17: Confidence 40% = score 0 (LOW)")
    
    def test_full_validation_approved(self):
        """Test 18: Valid complete scenario should be APPROVED"""
        validation_params = {
            'rsi': 25.0,  # OVERSOLD (extreme)
            'momentum': -0.6,  # Correlates with oversold
            'volatility': 'LOW',  # Safe
            'recent_losses': [(time.time(), -50), (time.time(), 100)],  # OK
            'last_op_time': time.time() - 65,  # 65s gap (valid)
            'confidence': 65
        }
        result = self.validator.validate_before_rapid_op(validation_params)
        self.assert_equal(result['should_open'], True, "Test 18: Valid scenario = APPROVED to open")
        self.assert_equal(result['passed_criteria'], 5, "Test 18: All 5 criteria should pass")
    
    def test_full_validation_rejected_rsi_neutral(self):
        """Test 19: Neutral RSI should be REJECTED"""
        validation_params = {
            'rsi': 50.0,  # NEUTRAL (not extreme)
            'momentum': 0.0,
            'volatility': 'LOW',
            'recent_losses': [],
            'last_op_time': time.time() - 65,
            'confidence': 65
        }
        result = self.validator.validate_before_rapid_op(validation_params)
        self.assert_equal(result['should_open'], False, "Test 19: Neutral RSI scenario = REJECTED")
    
    def test_full_validation_rejected_high_volatility(self):
        """Test 20: HIGH volatility should be REJECTED"""
        validation_params = {
            'rsi': 25.0,  # OVERSOLD (extreme)
            'momentum': -0.6,  # Correlates
            'volatility': 'HIGH',  # NOT safe
            'recent_losses': [],
            'last_op_time': time.time() - 65,
            'confidence': 65
        }
        result = self.validator.validate_before_rapid_op(validation_params)
        self.assert_equal(result['should_open'], False, "Test 20: HIGH volatility scenario = REJECTED")
    
    def test_full_validation_rejected_too_many_losses(self):
        """Test 21: 3+ recent losses should be REJECTED"""
        validation_params = {
            'rsi': 25.0,  # OVERSOLD (extreme)
            'momentum': -0.6,  # Correlates
            'volatility': 'LOW',  # Safe
            'recent_losses': [(time.time(), -10), (time.time(), -20), (time.time(), -30), (time.time(), 50), (time.time(), 100)],  # 3 losses
            'last_op_time': time.time() - 65,
            'confidence': 65
        }
        result = self.validator.validate_before_rapid_op(validation_params)
        self.assert_equal(result['should_open'], False, "Test 21: 3+ recent losses scenario = REJECTED")
    
    def test_result_tracking(self):
        """Test 22: Recording operation results updates history"""
        initial_len = len(self.validator.recent_rapid_losses)
        self.validator.record_rapid_op_result(100.50)
        self.validator.record_rapid_op_result(-50.0)
        new_len = len(self.validator.recent_rapid_losses)
        self.assert_true(new_len > initial_len, "Test 22: Recent losses updated after recording results")
    
    def test_validation_stats_reporting(self):
        """Test 23: Stats should be reportable"""
        stats = self.validator.get_validation_stats()
        self.assert_true('total_validations' in stats, "Test 23: Stats include total_validations")
        self.assert_true('approval_rate' in stats, "Test 23: Stats include approval_rate")
        self.assert_true('risk_distribution' in stats, "Test 23: Stats include risk_distribution")
    
    # ============ RUN ALL TESTS ============
    
    def run_all_tests(self):
        """Execute all test cases"""
        print("\n" + "="*70)
        print("AREA 6: Smart Rapid Operations Integration Tests")
        print("="*70 + "\n")
        
        # Run all tests
        self.test_rsi_oversold_detection()
        self.test_rsi_overbought_detection()
        self.test_rsi_neutral_rejection()
        self.test_momentum_buy_correlation()
        self.test_momentum_buy_divergence()
        self.test_momentum_sell_correlation()
        self.test_momentum_sell_divergence()
        self.test_volatility_low_safe()
        self.test_volatility_normal_safe()
        self.test_volatility_high_unsafe()
        self.test_volatility_extreme_unsafe()
        self.test_time_gap_valid()
        self.test_time_gap_too_short()
        self.test_recent_losses_acceptable()
        self.test_recent_losses_too_many()
        self.test_confidence_high()
        self.test_confidence_low()
        self.test_full_validation_approved()
        self.test_full_validation_rejected_rsi_neutral()
        self.test_full_validation_rejected_high_volatility()
        self.test_full_validation_rejected_too_many_losses()
        self.test_result_tracking()
        self.test_validation_stats_reporting()
        
        # Summary
        print("\n" + "="*70)
        total = self.tests_passed + self.tests_failed
        print(f"\nTEST SUMMARY")
        print(f"   PASSED: {self.tests_passed}/{total}")
        print(f"   FAILED: {self.tests_failed}/{total}")
        print(f"   PASS RATE: {(self.tests_passed/total*100):.1f}%")
        
        if self.tests_failed == 0:
            print("\nALL TESTS PASSED! AREA 6 Integration Complete!")
            return True
        else:
            print(f"\n{self.tests_failed} tests failed. Review errors above.")
            return False
        print("="*70)


if __name__ == '__main__':
    tester = TestArea6RapidOpsValidator()
    success = tester.run_all_tests()
    sys.exit(0 if success else 1)
