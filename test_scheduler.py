#!/usr/bin/env python3
"""Test scheduler timing precision"""
import time

def test_scheduler_precision():
    """Simulate scheduler with improved timing logic"""
    
    # Simulate interval of 10 seconds
    intervalo = 10.0
    
    # Set next open time
    next_open = time.time() + intervalo
    
    print(f"🔷 Scheduler Test: {intervalo}s interval")
    print(f"Start time: {time.time():.2f}")
    print(f"Next open: {next_open:.2f}")
    print("=" * 50)
    
    checks = 0
    opens = 0
    last_remaining = None
    
    while opens < 2:  # Run 2 cycles
        now = time.time()
        
        # NEW LOGIC: Check if it's time to open
        if now >= next_open:
            opens += 1
            print(f"\n🚀 FORCED OPEN #{opens} at {now:.2f}")
            print(f"   Scheduled for: {next_open:.2f}")
            print(f"   Precision: {abs(now - next_open):.3f}s error")
            next_open = now + intervalo
            checks = 0
            last_remaining = None
        else:
            # Calculate remaining time WITHOUT truncation (precision)
            remaining = next_open - now
            remaining_int = int(remaining)
            
            # Show countdown at each second boundary
            if last_remaining is None or remaining_int != last_remaining:
                last_remaining = remaining_int
                if remaining_int > 0:
                    bar = "█" * remaining_int + "░" * (int(intervalo) - remaining_int)
                    print(f"⏱️  [{bar}] {remaining_int}s remaining (actual: {remaining:.3f}s)")
        
        checks += 1
        
        # IMPROVED: Sleep 0.5s instead of 1s for precision
        time.sleep(0.5)
    
    print("\n✅ Test completed - timing precision verified")

if __name__ == '__main__':
    test_scheduler_precision()
