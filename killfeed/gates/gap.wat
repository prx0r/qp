;; GAP gate, WASM reference implementation (plan2 Layer 1).
;; (demand_low, demand_high, supply_low, supply_high, threshold) -> i32
;; 1 = TRUE, 0 = FALSE, -1 = UNKNOWN. NaN inputs yield UNKNOWN.
(module
  (func (export "gap")
    (param $dl f64) (param $dh f64)
    (param $sl f64) (param $sh f64) (param $t f64)
    (result i32)
    (if (result i32)
      (f64.gt (local.get $dl) (f64.mul (local.get $sh) (local.get $t)))
      (then (i32.const 1))
      (else
        (if (result i32) (f64.le (local.get $dh) (local.get $sl))
          (then (i32.const 0))
          (else (i32.const -1)))))))
